import subprocess
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ping 设置
PING_TIMEOUT = 5
PING_COUNT = 2

# 线程数
MAX_PARALLEL = 10

# host主机列表
HOSTS = [
    {'host': 'www.baidu.com', 'name': 'ok-01'},
    {'host': 'www.qq.com', 'name': 'ok-02'},
    {'host': '192.0.2.1', 'name': 'bad-01'},
    {'host': 'www.taobao.com', 'name': 'ok-03'},
    {'host': 'www.jd.com', 'name': 'ok-04'},
    {'host': 'www.aliyun.com', 'name': 'ok-05'},
    {'host': 'www.163.com', 'name': 'ok-06'},
    {'host': '192.0.2.2', 'name': 'bad-02'},
    {'host': 'www.sina.com.cn', 'name': 'ok-07'},
    {'host': 'www.sohu.com', 'name': 'ok-08'},
    {'host': 'www.zhihu.com', 'name': 'ok-09'},
    {'host': '192.0.2.3', 'name': 'bad-03'},
    {'host': 'www.bilibili.com', 'name': 'ok-10'},
    {'host': 'www.douyin.com', 'name': 'ok-11'},
    {'host': 'www.bytedance.com', 'name': 'ok-12'},
    {'host': '192.0.2.4', 'name': 'bad-04'},
    {'host': 'www.iqiyi.com', 'name': 'ok-13'},
    {'host': 'www.youku.com', 'name': 'ok-14'},
    {'host': 'www.weibo.com', 'name': 'ok-15'},
    {'host': 'www.douban.com', 'name': 'ok-16'},
    {'host': '192.0.2.5', 'name': 'bad-05'},
    {'host': 'www.csdn.net', 'name': 'ok-17'},
    {'host': 'www.cctv.com', 'name': 'ok-18'},
    {'host': 'www.gov.cn', 'name': 'ok-19'},
    {'host': '192.0.2.6', 'name': 'bad-06'},
    {'host': 'news.163.com', 'name': 'ok-20'},
    {'host': 'mail.qq.com', 'name': 'ok-21'},
    {'host': 'mail.163.com', 'name': 'ok-22'},
    {'host': '192.0.2.7', 'name': 'bad-07'},
    {'host': 'news.sina.com.cn', 'name': 'ok-23'},
    {'host': 'v.qq.com', 'name': 'ok-24'},
    {'host': 'tieba.baidu.com', 'name': 'ok-25'},
    {'host': 'pan.baidu.com', 'name': 'ok-26'},
    {'host': '192.0.2.8', 'name': 'bad-08'},
    {'host': 'weixin.qq.com', 'name': 'ok-27'},
    {'host': 'item.jd.com', 'name': 'ok-28'},
    {'host': 'www.tmall.com', 'name': 'ok-29'},
    {'host': '192.0.2.9', 'name': 'bad-09'},
    {'host': 'detail.tmall.com', 'name': 'ok-30'},
    {'host': 'm.baidu.com', 'name': 'ok-31'},
    {'host': 'zhidao.baidu.com', 'name': 'ok-32'},
    {'host': '192.0.2.10', 'name': 'bad-10'},
    {'host': 'wenku.baidu.com', 'name': 'ok-33'},
    {'host': 'help.aliyun.com', 'name': 'ok-34'},
    {'host': 'space.bilibili.com', 'name': 'ok-35'},
    {'host': 'news.sohu.com', 'name': 'ok-36'},
    {'host': '192.0.2.11', 'name': 'bad-11'},
    {'host': 'finance.sina.com.cn', 'name': 'ok-37'},
    {'host': 'sports.qq.com', 'name': 'ok-38'},
    {'host': 'book.jd.com', 'name': 'ok-39'},
    {'host': '192.0.2.12', 'name': 'bad-12'},
    {'host': 'www.126.com', 'name': 'ok-40'},
    {'host': 'mail.126.com', 'name': 'ok-41'},
    {'host': 'news.qq.com', 'name': 'ok-42'},
    {'host': '192.0.2.13', 'name': 'bad-13'},
    {'host': 'www.taobao.com', 'name': 'ok-43'},
    {'host': 'www.jd.com', 'name': 'ok-44'},
    {'host': 'www.people.com.cn', 'name': 'ok-45'},
    {'host': 'www.xinhuanet.com', 'name': 'ok-46'},
    {'host': '192.0.2.14', 'name': 'bad-14'},
    {'host': 'news.cctv.com', 'name': 'ok-47'},
    {'host': 'www.ifeng.com', 'name': 'ok-48'},
    {'host': 'www.china.com.cn', 'name': 'ok-49'},
    {'host': '192.0.2.15', 'name': 'bad-15'},
    {'host': 'www.12306.cn', 'name': 'ok-50'},
    {'host': 'www.ce.cn', 'name': 'ok-51'},
    {'host': 'bbs.hupu.com', 'name': 'ok-52'},
    {'host': '192.0.2.16', 'name': 'bad-16'},
    {'host': 'www.pptv.com', 'name': 'ok-53'},
    {'host': 'www.4399.com', 'name': 'ok-54'},
    {'host': 'news.baidu.com', 'name': 'ok-55'},
    {'host': 'baike.baidu.com', 'name': 'ok-56'},
    {'host': '198.51.100.1', 'name': 'bad-17'},
    {'host': 'image.baidu.com', 'name': 'ok-57'},
    {'host': 'map.baidu.com', 'name': 'ok-58'},
    {'host': 'fanyi.baidu.com', 'name': 'ok-59'},
    {'host': '198.51.100.2', 'name': 'bad-18'},
    {'host': 'cloud.tencent.com', 'name': 'ok-60'},
    {'host': 'www.tencent.com', 'name': 'ok-61'},
    {'host': 'docs.qq.com', 'name': 'ok-62'},
    {'host': '198.51.100.3', 'name': 'bad-19'},
    {'host': 'www.chinanews.com', 'name': 'ok-63'},
    {'host': 'www.youth.cn', 'name': 'ok-64'},
    {'host': 'www.mgtv.com', 'name': 'ok-65'},
    {'host': 'www.le.com', 'name': 'ok-66'},
    {'host': '198.51.100.4', 'name': 'bad-20'},
    {'host': 'www.meituan.com', 'name': 'ok-67'},
    {'host': 'www.dianping.com', 'name': 'ok-68'},
    {'host': 'www.ctrip.com', 'name': 'ok-69'},
    {'host': '198.51.100.5', 'name': 'bad-21'},
    {'host': 'www.pinduoduo.com', 'name': 'ok-70'},
    {'host': 'www.youzan.com', 'name': 'ok-71'},
    {'host': 'www.icbc.com.cn', 'name': 'ok-72'},
    {'host': '198.51.100.6', 'name': 'bad-22'},
    {'host': 'www.ccb.com', 'name': 'ok-73'},
    {'host': '223.5.5.5', 'name': 'ok-74'},
    {'host': '223.6.6.6', 'name': 'ok-75'},
    {'host': '119.29.29.29', 'name': 'ok-76'},
    {'host': '198.51.100.7', 'name': 'bad-23'},
    {'host': '180.76.76.76', 'name': 'ok-77'},
]


def log(msg: str) -> None:
    """
    日志输出与写入函数
    """
    time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    day_now = datetime.now().strftime('%Y-%m-%d')
    body = f"{time_now} | {msg}\n"
    with open(f"host_check_{day_now}.log", 'a', encoding='utf-8') as f:
        f.write(body)


print(body,end='')

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
        cmd_result = subprocess.run(cmd, capture_output=True, text=True,timeout=10)
    # 超时返回
    except subprocess.TimeoutExpired:
        log(f"error | name: {host_one['name']}, ip: {host_one['host']}, error info: ping命令超时")
        host_one_result['detail'] = 'ping命令超时'
        return host_one_result

    # 失败返回
    if cmd_result.returncode != 0:
        log(f"error | name: {host_one['name']}, ip: {host_one['host']}, error info: ping失败")
        host_one_result['detail'] = 'ping失败'
        return host_one_result


    # 获取延迟与丢包率
    out = cmd_result.stdout
    avg = loss = "N/A"
    for line in out.splitlines():
        if "平均" in line:
            avg = line.split('=')[3]
        if "丢失" in line:
            loss = line.split('=')[3].split('(')[0]

    # 成功返回
    host_one_result['result'] = 'SUCCESS'
    host_one_result['detail'] = f"loss: {loss}, avg: {avg}"

    log(f"info | name: {host_one['name']}, ip: {host_one['host']}, loss: {loss}, avg: {avg}")
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
                log(f"error | ip: {future_host}, error info: {e}")
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
    fail_count = 0

    print('-' * 50)
    print(f"最终探测报告，时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print('-' * 50)
    for r in results:
        status = "OK" if r['result'] == 'SUCCESS' else "FAIL"
        print(f"{status} | {r['name']:<15} | {r['host']:<15} | {r['detail']:<15}")

        if r['result'] == 'SUCCESS':
            success_count += 1
        else:
            fail_count += 1

    print('-' * 50)
    print(f"成功：{success_count}，失败：{fail_count}，总数:{success_count + fail_count}")
    print('-' * 50)

    return success_count, fail_count


def main():
    """
    1 运行多线程程序
    2 输出结果
    """
    success, failure = print_result(run_parallel(HOSTS))
    return 0 if failure == 0 else 1

if __name__ == '__main__':
    sys.exit(main())