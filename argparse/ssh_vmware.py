import sys
import logging
import subprocess
import ipaddress
import argparse
from pathlib import Path
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, as_completed



def get_args() -> argparse.Namespace:
    argparser = argparse.ArgumentParser(description='ssh巡检')
    argparser.add_argument('-u','--user',type=str,default='root',help='用户名')
    argparser.add_argument('-f','--hosts',type=str,default=Path(__file__).parent /'ssh.conf',help='配置清单')
    argparser.add_argument('--host',type=str,default=None,help='ip地址')
    argparser.add_argument('-p','--port',type=int,default=22,help='端口号')
    argparser.add_argument('-w','--workers',type=int, default=3, help='并发数')
    argparser.add_argument('--warning_percent',type=int,default=85,help='告警阈值')
    return argparser.parse_args()


def get_conf(path: Path) -> list:
    hosts = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line  in f:
                parts = line.strip().split(',')
                if line.startswith('#') or len(parts) != 3:
                    continue
                try:
                    ip = str(parts[0])
                    ipaddress.ip_address(ip)
                except ValueError:
                    log.error(f"{ip} ip地址错误 跳过")
                    continue
                try:
                    port = int(parts[1])
                except ValueError:
                    log.error(f"{ip} port类型错误，应该为int 跳过")
                    continue
                username = str(parts[2])
                hosts.append({'ip':ip, 'port':port, 'username':username})
    except FileNotFoundError:
        log.error(f"配置文件没找到 {path}")
        sys.exit(1)

    return hosts


def get_conf_argparse(args: argparse.Namespace) -> list:
    hosts = []
    try:
        ipaddress.ip_address(args.host)
    except ValueError:
        log.error(f"{args.host} 输入参数错误")
        sys.exit(1)
    hosts.append({'ip':args.host, 'port':args.port, 'username':args.user})
    return hosts



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



def get_info(msg: str) -> tuple:
    lines = msg.splitlines()
    if len(lines) < 2:
        return None
    part = lines[1].strip().split()
    if len(part) < 5:
        return None
    return part[1], part[2], part[3], part[4]

def run_cmd_one(host: dict,warning: int) -> dict:
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
        cmd_result["detail"] = f"连接超时（8秒内 ssh 未完成连接+执行）"
        log.error(f"{ssh_info} 连接超时（8秒内 ssh 未完成连接+执行）")
        return cmd_result

    if result.returncode == 255:
        cmd_result["detail"] = f"{result.stderr.strip()[:100]}"
        log.error(f"{ssh_info}, {result.stderr.strip()[:100]}")
        return cmd_result
    elif result.returncode != 0:
        cmd_result["detail"] = f"{result.stderr.strip()[:100]}"
        log.error(f"{ssh_info} {result.stderr.strip()[:100]}")
        return cmd_result

    info = get_info(result.stdout)
    if info is None:
        log.error(f"{ssh_info} 获取失败")
        cmd_result["status"] = "FAILURE"
        cmd_result["detail"] = "执行失败"
        cmd_result["result"] = {'size': 'error', 'used': 'error', 'avail': 'error', 'use_percent': 'error'}
        return cmd_result
    size, used, avail, use_p = info
    log.info(f"{ssh_info} 获取成功 Size:{size}, used:{used}, avail:{avail}, use_percent:{use_p}")
    cmd_result["status"] = "SUCCESS"
    cmd_result["detail"] = "执行成功"
    cmd_result["result"] = {'size':size, 'used':used, 'avail':avail, 'use_percent':use_p}

    if int(use_p.strip('%')) > int(warning):
        cmd_result["status"] = "WARNING"
        cmd_result["detail"] = f"磁盘使用超过{warning}%"
    return cmd_result

def run_cmd_parallel(hosts: list,workers: int,warning: int) -> list:

    last_list = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_list = {pool.submit(run_cmd_one,host,warning):host for host in hosts}
        for future in as_completed(future_list):
            host_info = future_list[future]
            try:
                result = future.result()
            except Exception as e:
                result = {
                    'ip': host_info['ip'],
                    'username': host_info['username'],
                    'status': 'FAILURE',
                    'detail': f"{host_info['username']}@{host_info['ip']} 命令执行失败, {str(e)}",
                    'result': {}
                }
                log.error(f"{host_info['username']}@{host_info['ip']} 命令执行失败")
            last_list.append(result)
    return last_list


def print_report(last_list: list) -> tuple:

    success = 0
    warning = 0
    failure = 0

    print('-'*50)
    print('-'*20,datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'-'*20)
    print('-'*50)

    for result in last_list:
        if result['status'] == 'SUCCESS':
            success += 1
        elif result['status'] == 'FAILURE':
            failure += 1
        elif result['status'] == 'WARNING':
            warning += 1
        print(f"{result['status']} | {result['username']}@{result['ip']:<18} | {result['detail']:<30} | size: {result['result'].get('size','error'):<10} | used: {result['result'].get('used','error'):<10} | avail: {result['result'].get('avail','error'):<10} | use_percent: {result['result'].get('use_percent','error'):<10} ")

    print('-'*50)
    print(f"成功 {success}，警告： {warning}, 失败 {failure}，共 {success + warning + failure} 台")
    return success, warning, failure



def main():
    """
    1 日志函数
    2 单个连接执行命令
    3 并发执行
    4 打印报告
    """

    setup_log()

    args = get_args()
    # 并发连接数
    workers = args.workers
    # 告警阈值
    threshold = args.warning_percent
    # 配置文件
    conf_file = args.hosts
    # 判断配置
    if args.host:
        hosts = get_conf_argparse(args)
    else:
        hosts = get_conf(conf_file)


    res = run_cmd_parallel(hosts,workers,threshold)
    success, warning, failure = print_report(res)

    return 0 if failure == 0 else 1

if __name__ == "__main__":
    sys.exit(main())