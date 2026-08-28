import shutil
import subprocess
import sys
import tarfile
import time
import re
import requests
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed

# pushgateway地址
PUSHGATEWAY_URL = "http://172.111.111.111:9091"

# 备份所在目录
EXPORT_DIR = Path("/root/live/to_98mysql")    # dump 输出目录
TAR_FILE = Path("/root/live/to_98mysql.tar.gz")
NAS_DIR = Path("/mnt/hubin02/to_98mysql")

# jenkins url
JENKINS_URL = ("http://192.111.111.111:8080/jenkins/view/rds-bak/"
               "job/rds-98-bak/build?token=rds-98-bak-token")
JENKINS_AUTH = ("job", "job123456")

# 命令集合
TASKS = [
    {"user":"backup_account","passwd":"123456789","host": "liveyu-report-db.mysql.rds.aliyuncs.com", "db": "report_db",
     "ignore": ["t_daily_cubby_trace", "t_reservation_channel_daily_report",
                "t_reservation_summary_daily_report", "t_page_statistic"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-report-db.mysql.rds.aliyuncs.com", "db": "report_data_db"},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-user-db.mysql.rds.aliyuncs.com", "db": "user_db",
     "fix_encryption": True},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-order-db.mysql.rds.aliyuncs.com", "db": "order_db",
     "ignore": ["t_energy_room_usage", "t_energy_room_usage_detail",
                "t_energy_room_usage_share", "t_guest_account_detail_0316bak",
                "t_invoice_apply_request_data", "t_order_20200327",
                "t_guest_account_detail", "t_finance_account_request"],
     "strip_definer": True},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-payment-db.mysql.rds.aliyuncs.com", "db": "payment_db",
     "ignore": ["t_third_payment_flow"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-product-db.mysql.rds.aliyuncs.com", "db": "product_db"},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-ota-db.mysql.rds.aliyuncs.com", "db": "ota_db",
     "ignore": ["t_channel_request_log"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-promotion-db.mysql.rds.aliyuncs.com", "db": "promotion_db",
     "ignore": ["t_client_utm_trace"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-community-db.mysql.rds.aliyuncs.com", "db": "community_db"},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-community-db.mysql.rds.aliyuncs.com", "db": "rag_db"},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-promotion-db.mysql.rds.aliyuncs.com", "db": "promotion_db",
     "table": ["t_coupon"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-ota-db.mysql.rds.aliyuncs.com", "db": "worktask_db"},
    {"user":"backup_account","passwd":"123456789","host": "building-activiti-db.mysql.rds.aliyuncs.com", "db": "pmp_db"},
    {"user":"backup_account","passwd":"123456789","host": "building-activiti-db.mysql.rds.aliyuncs.com", "db": "data_warehouse_db"},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-settlement-db.mysql.rds.aliyuncs.com", "db": "workbench_db"},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-content-db.mysql.rds.aliyuncs.com", "db": "content_db",
     "table": ["t_raw_data_msg"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-content-db.mysql.rds.aliyuncs.com", "db": "content_db",
     "table": ["t_questionnaire"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-content-db.mysql.rds.aliyuncs.com", "db": "content_db",
     "table": ["t_questionnaire_dispatch_task"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-content-db.mysql.rds.aliyuncs.com", "db": "content_db",
     "table": ["t_questionnaire_answer"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-content-db.mysql.rds.aliyuncs.com", "db": "content_db",
     "table": ["t_questionnaire_template_questions"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_dictionary"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_dictionary_data"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_ding_config"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_email_config"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_email_smtp_config"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_feishu_config"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_feishu_ding_message_code_mapper"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_inbox_config"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_message_config"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_nationality"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_push_config"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_region"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_script_history"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-main-db.mysql.rds.aliyuncs.com", "db": "main_db",
     "table": ["t_sms_config"]},
    {"user":"backup_account","passwd":"123456789","host": "ai-model-db.mysql.rds.aliyuncs.com", "db": "ai_model_db",
     "table": ["t_reservation_follow_llm_detail"]},
    {"user":"backup_account","passwd":"123456789","host": "ai-model-db.mysql.rds.aliyuncs.com", "db": "ai_model_db",
     "table": ["t_raw_data_msg_every_10_sentences_only_text"]},
    {"user":"backup_account","passwd":"123456789","host": "ai-model-db.mysql.rds.aliyuncs.com", "db": "ai_model_db",
     "table": ["t_sentiment_score_batch_new"]},
    {"user":"backup_account","passwd":"123456789","host": "ai-model-db.mysql.rds.aliyuncs.com", "db": "ai_model_db",
     "table": ["wechat_content_keyword_every_10_classified"]},
    {"user":"backup_account","passwd":"123456789","host": "ai-model-db.mysql.rds.aliyuncs.com", "db": "ai_model_db",
     "table": ["wechat_content_with_tags"]},
    {"user":"backup_account","passwd":"123456789","host": "ai-model-db.mysql.rds.aliyuncs.com", "db": "ai_model_db",
     "table": ["t_sentiment_score_diff_six_hours_customer_only_new"]},
    {"user":"backup_account","passwd":"123456789","host": "liveyu-report-db.mysql.rds.aliyuncs.com", "db": "report_db",
     "table": ["t_wework_reception_info"]},
]



def log(msg: str) -> None:
    """
    日志打印
    :param msg: str
    """
    log_date = datetime.now().strftime('%Y_%m_%d')
    log_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_body = f'{log_time} | {msg}'
    print(log_body)
    with open(f'mysqldump_{log_date}.log','a',encoding='utf-8') as f:
        f.write(f'{log_body}\n')

def get_host_ip() -> str:
    """
    linux系统获取本机ip
    :return: str
    """
    cmd = ['hostname','-I']
    resulte = subprocess.run(cmd,capture_output=True,text=True)
    return resulte.stdout.strip().split()[0]

def push_metrics(metrics: dict) -> None:
    """
    推送指标到pushgateway
    :param : dict，指标信息
    """
    host_ip = get_host_ip()
    full_url = PUSHGATEWAY_URL + f'/metrics/job/98mysqldump/Env/blue/instance/{host_ip}'
    body = ''.join(f'# TYPE {k} gauge\n{k} {v}\n' for k, v in metrics.items())
    try:
        respoens = requests.post(full_url, data=body, timeout=10)
        respoens.raise_for_status()
        log(f'info, push metrics success')
    except requests.RequestException as e:
        log(f'warn, push metrics error: {e}')

def delete_old_backup() -> None:
    """
    删除旧的备份文件与备份压缩包
    """
    # 删除目录下所有的文件
    for file in EXPORT_DIR.glob('*'):
        file.unlink()
        log(f'info, 旧备份文件 {file} 删除成功')
    log(f'info, 旧备份文件全部删除完成')
    # 删除压缩包
    TAR_FILE.unlink(missing_ok=True)
    log(f'info, 旧备份压缩包{TAR_FILE.name}删除完成')
    # 托底，创建备份目录
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def output_filename(task: dict) -> str:
    if task.get('table',[]):
        return f"{task['table'][0]}.sql"
    else:
        return  task['db'] + '.sql'

def dump_one(task: dict) -> bool:
    """

    """
    # 拼接mysqldump命令
    cmd = ["echo","--single-transaction=TRUE","--set-gtid-purged=OFF",f"-u{task['user']}",f"-p{task['passwd']}",f"-h{task['host']}",f"{task['db']}"]
    if task.get('table',[]):
        cmd.extend(task['table'])
    for ignore in task.get('ignore',[]):
        cmd.append(f"--ignore-table={task['db']}.{ignore}")

    # 生成导出sql的文件名
    output_file = output_filename(task)

    # 执行备份命令
    full_path_filename = EXPORT_DIR / output_file
    try:
        with open(full_path_filename,'w',encoding='utf-8') as f:
            subprocess.run(cmd,stdout=f,stderr=subprocess.PIPE,text=True,check=True)
        log(f"info, 备份文件{output_file}保存完成")
    except subprocess.CalledProcessError as e:
        log(f"error, 备份文件{output_file}出错,请稍后检查, {e}")
        full_path_filename.unlink(missing_ok=True)
        return False

    # 对特殊文件进行特殊处理
    path_f = EXPORT_DIR / output_file
    if task.get('fix_encryption', False):
        replace_in_file(path_f, "ENCRYPTION='Y'", "ENCRYPTION='N'")

    if task.get('strip_definer', False):
        # 正则替换
        regx_replace_in_file(path_f, r"DEFINER[ ]*=[ ]*[^*]*\*", '*')
    return True

def replace_in_file(file: Path, old_str: str, new_str: str) -> None:
    """
    对文件的字符进行替换，流式输出
    """
    tmp_file = file.with_suffix('.tmp')
    with open(file, 'r', encoding='utf-8') as f, \
        open(tmp_file,'w',encoding='utf-8') as t:
        for line in f:
            t.write(line.replace(old_str, new_str))
    tmp_file.replace(file)

def regx_replace_in_file(file: Path, regx: str, new_str: str) -> None:
    """
    使用正则表达式对文件内容进行替换，流式输出
    """
    tmp_file = file.with_suffix('.tmp')
    compiled = re.compile(regx)
    with open(file, 'r', encoding='utf-8') as f, \
        open(tmp_file,'w',encoding='utf-8') as t:
        for line in f:
            t.write(compiled.sub(new_str,line))
    tmp_file.replace(file)

def run_parallel(tasks: list) -> tuple:
    """
    1. 循环列表里的任务
    2. 并发运行每个任务
    3. 对有需要的sql文件进行特殊处理
    """
    success = 0
    failure = 0
    with ThreadPoolExecutor(max_workers=4) as T:
        future_list = {T.submit(dump_one,task):task for task in tasks}
        for future in as_completed(future_list):
            cmd_dict = future_list[future]
            name_f = output_filename(cmd_dict)

            try:
                ok = future.result()
            except Exception as e:
                log(f"error, {name_f} 执行出错，{e}")
                ok = False
            if ok:
                success += 1
            else:
                failure += 1

    return success, failure

def pack_and_compress() -> None:
    with tarfile.open(TAR_FILE,'w:gz') as tar:
        tar.add(EXPORT_DIR,arcname=EXPORT_DIR.name)

def upload_nas() -> None:
    NAS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(TAR_FILE, NAS_DIR / TAR_FILE.name)

def trigger_pipeline():
    try:
        response = requests.post(JENKINS_URL, auth=JENKINS_AUTH, timeout=5)
        response.raise_for_status()
        log(f"info, Jenkins pipeline触发成功")
    except Exception as e:
        log(f"error,触发Jenkins失败, {e}")


def main():
    """
     1 推送开始的指标
     2 删除旧备份
     3 并发运行dump命令
     4 制作压缩包
     5 上传 NAS
     6 触发 Jenkins
     7 推送指标
    """

    # 1
    time_start = time.time()
    push_metrics({'start_job_time': time_start})

    # 2
    delete_old_backup()

    # 3
    s,f = run_parallel(TASKS)
    log(f"info, 成功数量：{s}, 失败数量：{f}")

    # 4
    pack_and_compress()

    # 5
    upload_nas()

    # 6
    trigger_pipeline()

    # 7
    time_end = time.time()
    push_metrics({'end_job_time': time_end})

    # 8
    return 0 if f == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
