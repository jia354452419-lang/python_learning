#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量主机巡检工具（第一期：ping 探活 + 可扩展检查项）

教学说明：
  这个脚本和您的备份脚本是"同一个骨架，换一身皮"：
    TASKS 列表        →  HOSTS 列表
    dump_one()        →  check_one()
    并发收果逻辑       →  几乎原样照搬
    退出码            →  全部正常 0，有异常 1

学习路径建议：
  1. 先通读 main()，理解整体流程
  2. 再读 check_one()，理解单机检查怎么写
  3. 最后读 run_parallel()，和备份脚本对比异同
  4. 看懂后合上文件，自己默写一遍
"""

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ==================== 配置区 ====================

MAX_PARALLEL = 20          # 巡检是轻量任务，并发可以比备份开得多
PING_COUNT = 2             # ping 几个包
PING_TIMEOUT = 2           # 单个包超时（秒）

# 巡检对象列表：真实环境可以从文件/CMDB 读取，这里先写死几个示例
HOSTS = [
    {"ip": "www.baidu.com", "name": "web-01"},
    {"ip": "192.168.96.11", "name": "web-02"},
    {"ip": "192.168.96.12", "name": "db-01"},
    {"ip": "10.255.255.1",  "name": "不存在的主机"},   # 用来验证失败路径
]


# ==================== 工具函数 ====================

def log(msg: str) -> None:
    """日志：屏幕 + 按天滚动的文件（从备份脚本搬来的老熟人）"""
    now = datetime.now()
    line = f"{now.strftime('%Y-%m-%d %H:%M:%S')} | {msg}"
    print(line)
    with open(f"host_check_{now.strftime('%Y_%m_%d')}.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ==================== 核心：单机检查 ====================

def check_one(host: dict) -> dict:
    """
    检查一台主机，返回结果字典。

    注意返回值设计：不再只是 True/False，而是一个字典——
    因为巡检要汇报"哪里异常、异常是什么"，信息量比备份大。
    这正是"返回值契约随业务需求变化"的例子。
    """
    result = {
        "ip": host["ip"],
        "name": host["name"],
        "ok": False,          # 整体是否通过
        "detail": "",         # 异常原因（通过时为空）
    }

    # ---- 检查项 1：ping 探活 ----
    # -c: 包数量  -W: 单包超时秒数（Linux ping 的参数）
    cmd = ["ping", "-c", str(PING_COUNT), "-W", str(PING_TIMEOUT), host["ip"]]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        # subprocess 自己的总超时（比 ping 内部的 -W 更靠外的一层保险）
        result["detail"] = "ping 命令整体超时"
        return result

    if proc.returncode != 0:
        result["detail"] = "ping 不通"
        return result

    # ---- 检查项 2（示例扩展位）：丢包率解析 ----
    # ping 输出里有 "0% packet loss"，可以用正则抠出来判断质量
    # 留给您练手：用 re.search(r"(\d+)% packet loss", proc.stdout) 试试

    result["ok"] = True
    return result


# ==================== 并发调度（和备份脚本几乎一样） ====================

def run_parallel(hosts: list) -> list:
    """
    并发检查所有主机，返回结果列表。
    和备份脚本唯一的区别：返回的是结果对象列表，而不是成功/失败计数——
    因为巡检报告需要每台机器的详细信息。
    """
    log(f"开始巡检，共 {len(hosts)} 台，并发数 {MAX_PARALLEL}")
    results = []

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        # 老套路：future → 主机信息 的映射字典，完成后反查用
        future_to_host = {pool.submit(check_one, h): h for h in hosts}

        for future in as_completed(future_to_host):
            host = future_to_host[future]
            try:
                result = future.result()
            except Exception as e:
                # 薄兜底：check_one 里没接住的意外（bug、环境问题）
                result = {"ip": host["ip"], "name": host["name"],
                          "ok": False, "detail": f"检查过程异常: {e}"}
            results.append(result)

    return results


# ==================== 报告输出 ====================

def print_report(results: list) -> tuple:
    """
    打印巡检报告，返回 (正常数, 异常数)。
    小知识点：sorted 按 ok 排序，让异常的排在后面集中展示。
    """
    ok_count = 0
    fail_count = 0

    print("=" * 55)
    print(f"巡检报告 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    for r in sorted(results, key=lambda x: x["ok"], reverse=True):
        status = "OK  " if r["ok"] else "FAIL"
        # f-string 的对齐语法：{值:<15} 左对齐占 15 字符宽，让表格整齐
        print(f"[{status}] {r['ip']:<15} {r['name']:<12} {r['detail']}")
        if r["ok"]:
            ok_count += 1
        else:
            fail_count += 1

    print("-" * 55)
    print(f"汇总：{len(results)} 台 | 正常 {ok_count} | 异常 {fail_count}")
    return ok_count, fail_count


# ==================== 主流程 ====================

def main() -> int:
    results = run_parallel(HOSTS)
    _, fail_count = print_report(results)

    # 退出码：有异常主机返回 1，方便 crontab/监控判断
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
