# auth: Anbo Jia
# date: 2026-08-26
# from: trae

import time
import shutil
import sys
import tarfile
import re
import subprocess
import requests
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed


# pushgateway信息
PUSHGATEWAY ="http://172.19.205.251:9091"
ENV = 'Taoze'

# jenkins url
JENKINS_URL = ("http://192.168.102.120:8080/jenkins/view/rds-bak/"
               "job/rds-98-bak/build?token=rds-98-bak-token")
JENKINS_AUTH = ("job", "job123456")

# 线程数量
MAX_PARALLEL = 4

# 备份所在目录
EXPORT_DIR = Path("/opt/live/to_98mysql")    # dump 输出目录
TAR_FILE = Path("/root/live/to_98mysql.tar.gz")
NAS_DIR = Path("/mnt/hubin02/to_98mysql")

# 数据库账号密码
DB_USER = "backup_account"
DB_PASSWD = "Aa123456QWERTY"

TASKS = [
    {"host": "liveyu-report-db.mysql.rds.aliyuncs.com", "db": "report_db",
     "ignore": ["t_daily_cubby_trace", "t_reservation_channel_daily_report",
                "t_reservation_summary_daily_report", "t_page_statistic"]},
    {"host": "liveyu-report-db.mysql.rds.aliyuncs.com", "db": "report_data_db"},
    {"host": "liveyu-user-db.mysql.rds.aliyuncs.com", "db": "user_db",
     "fix_encryption": True},
    {"host": "liveyu-order-db.mysql.rds.aliyuncs.com", "db": "order_db",
     "ignore": ["t_energy_room_usage", "t_energy_room_usage_detail",
                "t_energy_room_usage_share", "t_guest_account_detail_0316bak",
                "t_invoice_apply_request_data", "t_order_20200327",
                "t_guest_account_detail", "t_finance_account_request"],
     "strip_definer": True},
    {"host": "liveyu-payment-db.mysql.rds.aliyuncs.com", "db": "payment_db",
     "ignore": ["t_third_payment_flow"]},
    {"host": "liveyu-product-db.mysql.rds.aliyuncs.com", "db": "product_db"},
    {"host": "liveyu-ota-db.mysql.rds.aliyuncs.com", "db": "ota_db",
     "ignore": ["t_channel_request_log"]},
    {"host": "liveyu-promotion-db.mysql.rds.aliyuncs.com", "db": "promotion_db",
     "ignore": ["t_client_utm_trace"]},
    {"host": "liveyu-community-db.mysql.rds.aliyuncs.com", "db": "community_db"},
    {"host": "liveyu-community-db.mysql.rds.aliyuncs.com", "db": "rag_db"},
    {"host": "liveyu-promotion-db.mysql.rds.aliyuncs.com", "db": "promotion_db",
     "table": ["t_coupon"]},
    {"host": "liveyu-ota-db.mysql.rds.aliyuncs.com", "db": "worktask_db"},
    {"host": "building-activiti-db.mysql.rds.aliyuncs.com", "db": "pmp_db"},
    {"host": "building-activiti-db.mysql.rds.aliyuncs.com", "db": "data_warehouse_db"},
    {"host": "liveyu-settlement-db.mysql.rds.aliyuncs.com", "db": "workbench_db"},
    {"host": "liveyu-content-db.mysql.rds.aliyuncs.com", "db": "content_db",
     "table": ["t_raw_data_msg"]},
    {"host": "liveyu-content-db.mysql.rds.aliyuncs.com", "db": "content_db",
     "table": ["t_questionnaire"]},
    {"host": "liveyu-content-db.mysql.rds.aliyuncs.com", "db": "content_db",
     "table": ["t_questionnaire_dispatch_task"]},
    {"host": "liveyu-content-db.mysql.rds.aliyuncs.com", "db": "content_db",
     "table": ["t_questionnaire_answer"]},
    {"host": "liveyu-content-db.mysql.rds.aliyuncs.com", "db": "content_db",
     "table": ["t_questionnaire_template_questions"]},
    {"host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_dictionary"]},
    {"host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_dictionary_data"]},
    {"host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_ding_config"]},
    {"host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_email_config"]},
    {"host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_email_smtp_config"]},
    {"host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_feishu_config"]},
    {"host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_feishu_ding_message_code_mapper"]},
    {"host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_inbox_config"]},
    {"host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_message_config"]},
    {"host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_nationality"]},
    {"host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_push_config"]},
    {"host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_region"]},
    {"host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_script_history"]},
    {"host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_sms_config"]},
    {"host": "ai-model-db.mysql.rds.aliyuncs.com", "db": "ai_model_db",
     "table": ["t_reservation_follow_llm_detail"]},
    {"host": "ai-model-db.mysql.rds.aliyuncs.com", "db": "ai_model_db",
     "table": ["t_raw_data_msg_every_10_sentences_only_text"]},
    {"host": "ai-model-db.mysql.rds.aliyuncs.com", "db": "ai_model_db",
     "table": ["t_sentiment_score_batch_new"]},
    {"host": "ai-model-db.mysql.rds.aliyuncs.com", "db": "ai_model_db",
     "table": ["wechat_content_keyword_every_10_classified"]},
    {"host": "ai-model-db.mysql.rds.aliyuncs.com", "db": "ai_model_db",
     "table": ["wechat_content_with_tags"]},
    {"host": "ai-model-db.mysql.rds.aliyuncs.com", "db": "ai_model_db",
     "table": ["t_sentiment_score_diff_six_hours_customer_only_new"]},
    {"host": "liveyu-report-db.mysql.rds.aliyuncs.com", "db": "report_db",
     "table": ["t_wework_reception_info"]},
]


def get_host_ip() -> str:
    '''
    获取linux系统的本机ip
    '''
    try:
        result = subprocess.run(["hostname","-I"],capture_output=True,text=True)
        return result.stdout.split(' ')[0]
    except Exception:
        return 'unknown'

def push_metrics(metrics) -> None:
    '''
    通过post方式发送指标到pushgateway
    :param metrics: 字典
    '''
    host_ip = get_host_ip()
    url = f"{PUSHGATEWAY}/metrics/job/{ENV}-job_crontab/instance/{host_ip}/env/{ENV}"
    # 发送数据: job_last_execute_start_time  time_job_start
    mes_body = ''.join(f'# TYPE {key} gauge\n{key} {value}\n'  for key,value in metrics.items())
    try:
        response = requests.post(url,data=mes_body,timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        log(f'warn,Push metrics error,{e}')

def log(mes) -> None:
    '''
    在本地生成日志，创建mysqldump.log文件
    :param mes: 字符串
    '''
    time_now = datetime.now()
    whole_msg = f'{time_now.strftime("%Y/%m/%d %H:%M:%S")} | {mes}\n'
    with open('mysqldump.log','a',encoding='utf-8') as f:
        f.write(whole_msg)
    print(whole_msg,end='')

def delete_old_backup() -> None:
    '''
    删除本地旧的备份sql与旧的压缩包，删除共享存储下的备份压缩包
    使用的是pathlib
    '''
    # 删除每一个sql文件
    for file in EXPORT_DIR.glob('*'):
        file.unlink()
    # 删除本地压缩包
    TAR_FILE.unlink(missing_ok=True)
    # 删除共享存储里的备份压缩包
    (NAS_DIR / TAR_FILE.name).unlink(missing_ok=True)
    # 托底，创建备份目录
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def build_dump_cmd(cmd_dict:dict) -> list:
    '''
    处理ignore表与单独备份表，把命令拼接
    :param cmd_dict: 字典
    :return: 一个mysqldump命令的列表
    '''
    cmd = ['mysqldump','--single-transaction=TRUE','--set-gtid-purged=OFF',f'-u{DB_USER}',f'-p{DB_PASSWD}',f"-h{cmd_dict['host']}",f"{cmd_dict['db']}"]
    for ignore_table in cmd_dict.get('ignore',[]):
        cmd.append(f"--ignore-table={cmd_dict['db']}.{ignore_table}")
    cmd.extend(f'{table}' for table in cmd_dict.get('table',[]))
    return cmd

def replace_in_file(path: Path, old: str, new: str) -> None:
    '''
    对文件内容进行替换，类似sed命令，一行一行读取如果匹配到，则替换,流式输出
    :param path: Path类型，路径
    :param old: 字符串
    :param new: 字符串
    '''
    tmp_file = path.with_suffix('.sql.tmp')
    with open(path,'r',encoding='utf-8') as p, \
        open(tmp_file,'w',encoding='utf-8') as t:
        for line in p:
            # str.replace(old_str,new_str)方法：将旧的字符串替换为新的字符串
            t.write(line.replace(old,new))
    # Path.replace()方法：文件改名，类似于linux中的mv
    tmp_file.replace(path)

def regex_replace_in_file(path: Path, regex: str, target: str) -> None:
    '''
    使用正则表达式对语句处理，流式输出
    :param path: Path 路径
    :param regex: str 正则表达式构建需要替换的部分
    :param target: str 替换的值
    '''
    regex_compiled = re.compile(regex)
    tmp_file = path.with_suffix('.sql.tmp')
    with open(path,'r',encoding='utf-8') as p, open(tmp_file,'w',encoding='utf-8') as t:
        for line in p:
            t.write(regex_compiled.sub(target,line))
    tmp_file.replace(path)

def output_filename(task_one:dict) -> Path:
    '''
    根据task，设置sql文件的名称
    :param task_one: 字典
    :return: 路径
    '''
    table = task_one.get("table")
    name = table[0] if table else task_one.get("db")
    return EXPORT_DIR / f'{name}.sql'

def dump_one(task_one: dict) -> bool:
    '''
    执行一个mysqldump命令，并且对有需要的sql内容进行替换
    :param task_one: 字典
    :return: 布尔
    '''
    out_file = output_filename(task_one)
    cmd = build_dump_cmd(task_one)
    try:
        with open(out_file,'w',encoding='utf-8') as o:
            subprocess.run(cmd, stdout=o, stderr=subprocess.PIPE,text=True, check=True)
    except subprocess.CalledProcessError as e:
        log(f"任务失败 {out_file.name}: {e.stderr.strip()[:200]}")
        out_file.unlink(missing_ok=True)
        return False

    if task_one.get("fix_encryption"):
        replace_in_file(out_file, "ENCRYPTION='Y'", "ENCRYPTION='N'")
    if task_one.get("strip_definer"):
        regex_replace_in_file(out_file, r"DEFINER[ ]*=[ ]*[^*]*\*","*")

    return True

def run_parallel(tasks: list) -> None:

    log(f"数据开始dump，并发数{MAX_PARALLEL}")
    success = 0
    failure = 0

    with ThreadPoolExecutor(MAX_PARALLEL) as T:
        task_dict = {T.submit(dump_one, t): t for t in tasks}
        for task in as_completed(task_dict):
            task_info = task_dict[task]
            name = output_filename(task_info).name

            try:
                ok = task.result()
            except Exception as e:
                log(f"任务失败 {name}: {e}")
                ok = False

            if ok:
                success += 1
            else:
                failure += 1

    return success, failure

def pack_and_distribute() -> None:
    with tarfile.open(TAR_FILE,'w:gz') as t:
        t.add(EXPORT_DIR, arcname=EXPORT_DIR.name)
    NAS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(TAR_FILE, NAS_DIR / TAR_FILE.name)
    log(f"备份传递nas完成")

def trigger_jenkins() -> None:
    try:
        response = requests.post(JENKINS_URL,auth=JENKINS_AUTH,timeout=15)
        response.raise_for_status()
        log(f"Jenkins触发成功！")
    except Exception as e:
        log(f"warn, 触发Jenkins失败，{e}")

def main():

    time_start = time.time()
    # 1. 开始推送指标
    push_metrics({"job_last_excute_time": time_start})

    # 2.清理旧备份
    delete_old_backup()

    # 3. 并发备份
    success, failure = run_parallel(TASKS)
    log(f"数据dump完毕！成功：{success}，失败：{failure}")

    # 4. 打包分发
    pack_and_distribute()

    # 5. 触发Jenkins
    trigger_jenkins()

    # 6. 推送最终状态（result: 0=全部成功， 1=有失败）
    time_end = int(time.time())
    push_metrics({
        "job_last_execute_end_time": time_end,
        "job_last_execute_result": 0 if failure == 0 else 1,
        "job_last_execute_duration": time_end - time_start,
    })

    return 0 if failure == 0 else 1

if __name__ == "__main__":
    sys.exit(main())












































