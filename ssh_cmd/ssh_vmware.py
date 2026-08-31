import sys
import logging
import subprocess
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, as_completed


HOSTS = [
    {'ip':'192.168.102.20','port':22,'username':'root','password':'root'},
    {'ip':'192.168.102.22','port':22,'username':'root','password':'root'},
]




# 日志函数
log = logging.getLogger(__name__)
def setup_log() -> None:
    log.setLevel(logging.DEBUG)

    screen_log = logging.StreamHandler(sys.stdout)
    screen_log.setLevel(logging.INFO)
    screen_log.setFormatter(logging.Formatter('%(asctime)s - %(levelname)-6s - %(message)s'))


    refresh_time_log = TimedRotatingFileHandler(
        Path(__file__).parent / "ssh_log.log", when="midnight",backupCount=2, encoding="utf-8"
    )
    refresh_time_log.setLevel(logging.DEBUG)
    refresh_time_log.setFormatter(logging.Formatter('%(asctime)s - %(name)-10s - %(levelname)-6s - %(message)s'))

    log.addHandler(screen_log)
    log.addHandler(refresh_time_log)



def get_info(msg: str):
    for line in msg.splitlines():
        if '/' in line:
            size = line.strip().split()[1]
            used = line.strip().split()[2]
            avail = line.strip().split()[3]
            use_p = line.strip().split()[4]
            return size, used, avail, use_p
    return None

def run_cmd_one(host: dict) -> dict:
    cmd = ["ssh", "-o", "BatchMode=yes",
           "-o", "ConnectTimeout=5",
           "-o", "StrictHostKeyChecking=accept-new",
           f"{host['username']}@{host['ip']}",
           "-p", f"{host['port']}",
           "df -h /"]
    """
    BatchMode=yes	没人输密码，避免脚本卡死
    ConnectTimeout=5	TCP 连接层超时（机器宕了 5 秒放弃，不等 subprocess 总超时）
    StrictHostKeyChecking=accept-new	第一次连新机器会问 yes/no → 脚本卡死；此参数自动接受新指纹（老指纹变了仍然拒绝，安全）
    """

    # 返回值
    cmd_result = {
        "ip": host['ip'],
        "username": host['username'],
        "status": "FAILURE",
        "detail": "",
        "result": {}
    }

    ssh_info = host["username"] + '@' + host["ip"]

    try:
        result = subprocess.run(cmd,capture_output=True,text=True,timeout=8)
    except subprocess.TimeoutExpired:
        cmd_result["detail"] = "连接超时，无法连接到目标主机"
        log.error(f"{ssh_info} 连接超时")
        return cmd_result

    if result.returncode == 255:
        cmd_result["detail"] = "命令输入有误"
        log.error(f"{ssh_info} 命令输入有误")
        return cmd_result
    elif result.returncode != 0:
        cmd_result["detail"] = "命令执行失败"
        log.error(f"{ssh_info} 命令执行失败")
        return cmd_result

    size, used, avail, use_p = get_info(result.stdout)
    log.info(f"{ssh_info} 获取成功 Size:{size}, used:{used}, avail:{avail}, use%:{use_p}")
    cmd_result["status"] = "SUCCESS"
    cmd_result["detail"] = "执行成功"
    cmd_result["result"] = {'size':size, 'used':used, 'avail':avail, 'use%':use_p}
    return cmd_result

def run_cmd_paralell(hosts: list) -> dict:

    last_list = []

    with ThreadPoolExecutor(max_workers=3) as pool:
        future_list = {pool.submit(run_cmd_one,host):host for host in hosts}
        for future in as_completed(future_list):
            host_info = future_list[future]
            try:
                result = future.result()
            except Exception as e:
                cmd_result = {
                    'ip': host_info['ip'],
                    'username': host_info['username'],
                    'status': 'FAILURE',
                    'detail': f"{host_info['username']}@{host_info['ip']} 命令执行失败, {str(e)}",
                    'result': {}
                }
                log.error(f"{host_info['username']}@{host_info['ip']} 命令执行失败")
                last_list.append(cmd_result)
            last_list.append(result)
    return last_list


def print_report(last_list: list) -> tuple:

    for result in last_list:
        print(f"{result['status']} | {result['username']}@{result['ip']:<18} | size: {result['result']['size']:<10} | used: {result['result']['used']:<10} | avail: {result['result']['avail']:<10} | use%: {result['result']['use%']:<10} ")




def main():
    """
    1 日志函数
    2 单个连接执行命令
    3 并发执行
    4 打印报告
    """
    setup_log()
    a = run_cmd_paralell(HOSTS)
    print_report(a)



if __name__ == "__main__":
    main()