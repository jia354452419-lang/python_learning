"""
1. windows 系统的ping -n 对应linux -c， -w的单位是ms linux -W是s
2. 状态常量STATUS_LIST={} 可以设置字典，通过status = STATUS_LIST[r['result']], 状态大于两种
3. status = 'OK' if r['result'] == 'SUCCESS' else 'FAIL' ， 状态只有两种的时候 可以用表达式
4. log（）函数需要进行线程锁，不然并发太多的时候会导致个别日志被吞掉
5. sorted 排序
6. print(f"{status} | {r['name']:<15} | {r['host']:<25} | {r['detail']:<35}")  设置输出格式
7. dict.get()可以设置默认值, dict.get('name',''),   而dict['name']只能取值，当key不存在时会报错
8. 正常的logging.StreamHandler的输出是走stderr（标准错误），而程序输出打印结果是stdout，所以会出现日志与最后的结果打印顺序不对，可以指定Handle的输出为stdout解决这个问题
"""

import logging
import re
import subprocess
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler


# ping 设置
PING_TIMEOUT = 5000
PING_COUNT = 2

# 线程数
MAX_PARALLEL = 10


# 获取配置文件
HOSTS = []
with open(Path(__file__).parent / 'hosts.txt','r',encoding='utf-8') as hosts:
    for line in hosts:
        line = line.strip()
        if not line:
            continue
        ip, name = line.split(',')
        HOSTS.append({'host': ip, 'name': name})




# log_lock = threading.Lock()
#
# def log(msg: str) -> None:
#     """
#     日志输出与写入函数
#     """
#     date_time = datetime.now()
#     time_now = date_time.strftime('%Y-%m-%d %H:%M:%S')
#     day_now = date_time.strftime('%Y-%m-%d')
#     body = f"{time_now} | {msg}\n"
#     with log_lock:
#         with open(f"host_check_{day_now}.log", 'a', encoding='utf-8') as f:
#             f.write(body)
#         print(body,end='')

# 日志
log = logging.getLogger('host_check')
def log_setup() -> None:

    log.setLevel(logging.DEBUG)

    screen_log = logging.StreamHandler(sys.stdout)
    screen_log.setLevel(logging.INFO)
    screen_log.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)-10s - %(message)s'))

    refresh_file_log = TimedRotatingFileHandler(Path(__file__).parent / 'host_check.log', when='midnight',backupCount=2, encoding='utf-8')
    refresh_file_log.setLevel(logging.DEBUG)
    refresh_file_log.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)-10s - %(message)s'))

    log.addHandler(screen_log)
    log.addHandler(refresh_file_log)



def check_host_one(host_one: dict) -> dict:
    """
    单个Host检查函数
    :return: dict
    """
    host_one_result = {
        "host": host_one['host'],
        "name": host_one['name'],
        "result": 'FAILURE',
        "detail": ""
    }

    # log(f"info | 开启任务： name: {host_one['name']}, ip: {host_one['host']}")

    cmd = ["ping","-n",str(PING_COUNT),"-w",str(PING_TIMEOUT),host_one['host']]
    try:
        cmd_result = subprocess.run(cmd, capture_output=True, text=True,timeout=15)
    # 超时返回
    except subprocess.TimeoutExpired:
        log.error(f"name: {host_one['name']:<10}, ip: {host_one['host']:<15}, error info: ping命令超时")
        host_one_result['detail'] = 'ping命令超时'
        return host_one_result

    # 失败返回
    if cmd_result.returncode != 0:
        log.error(f"name: {host_one['name']:<10}, ip: {host_one['host']:<15}, error info: ping失败")
        host_one_result['detail'] = 'ping失败'
        return host_one_result


    # 获取延迟与丢包率
    out = cmd_result.stdout
    avg =  'N/A'
    loss = None
    for line in out.splitlines():
        m = re.search(r'(\d+)%',line)
        if m:
            loss = int(m.group(1))
        m = re.search(r'(\d+)ms\s*$',line)
        if m:
            avg = m.group(1)
    if loss is None:
        host_one_result['result'] = 'WARN'
        host_one_result['detail'] = f"loss解析失败, avg: {avg}ms"
        log.error(f"name: {host_one['name']:<10}, ip: {host_one['host']:<15}, 'loss解析失败', avg: {avg}ms")
        return host_one_result

    if loss >= 50:
        host_one_result['result'] = 'WARN'
        host_one_result['detail'] = f"high loss, loss: {loss}%, avg: {avg}ms"
        log.warning(f"name: {host_one['name']:<10}, ip: {host_one['host']:<15}, loss: {loss}%, avg: {avg}ms")
        return host_one_result
    # 成功返回
    host_one_result['result'] = 'SUCCESS'
    host_one_result['detail'] = f"loss: {loss}%, avg: {avg}ms"

    log.info(f"name: {host_one['name']:<10}, ip: {host_one['host']:<15}, loss: {loss}%, avg: {avg}ms")
    return host_one_result


def run_parallel(hosts: list) -> list:
    """
    并发主程序，调用check_host_one()函数
    :param hosts: list
    :return: list
    """
    results = []
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        work_list = {pool.submit(check_host_one, host): host for host in hosts}
        for future in as_completed(work_list):
            future_host = work_list[future]
            try:
                result = future.result()
            except Exception as e:
                log.error(f"ip: {future_host}, error info: {e}")
                result = {
                    "host": future_host['host'],
                    "name": future_host['name'],
                    "result": 'FAILURE',
                    "detail": str(e)
                }

            results.append(result)
    return results

def print_result(results: list) -> tuple:
    """
    输出报告
    :param results: list
    :return: tuple
    """
    success_count = 0
    warn_count = 0
    fail_count = 0

    status_list = {
        'SUCCESS' : 'OK  ',
        'WARN' : 'WARN',
        'FAILURE' : 'FAIL',
    }

    print('-' * 50)
    print(f"最终探测报告，时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print('-' * 50)
    for r in sorted(results, key=lambda x: x["result"], reverse=True):
        status = status_list[r["result"]]
        print(f"{status} | {r['name']:<15} | {r['host']:<25} | {r['detail']:<35}")

        if r['result'] == 'SUCCESS':
            success_count += 1
        elif r['result'] == 'WARN':
            warn_count += 1
        else:
            fail_count += 1

    print('-' * 50)
    print(f"成功：{success_count}，警告：{warn_count}，失败：{fail_count}，总数:{success_count + warn_count + fail_count}")
    print('-' * 50)

    return success_count, warn_count, fail_count


def main():
    """
    1 运行多线程程序
    2 输出结果
    """
    log_setup()
    success, warn, failure = print_result(run_parallel(HOSTS))
    return 0 if failure == 0 else 1

if __name__ == '__main__':
    sys.exit(main())