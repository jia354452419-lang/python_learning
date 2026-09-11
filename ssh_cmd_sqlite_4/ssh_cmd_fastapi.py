import time
import os
import ssh_vmware
import hmac
from fastapi import FastAPI, BackgroundTasks, HTTPException, dependencies, Depends, Header
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
from prometheus_client import Counter, Gauge, generate_latest
from fastapi.responses import PlainTextResponse
from ssh_cmd_db import create_db




# 指标暴露设置
# Counter
check_runs_total = Counter("check_runs_total", "巡检总次数")
check_success_total = Counter("check_success_total","巡检成功总次数")
check_warning_total = Counter("check_warning_total","巡检警告总次数")
check_failure_total = Counter("check_failure_total","巡检失败总次数")
# Gauge
check_success_latest = Gauge("check_success_latest","最新巡检成功次数")
check_failure_latest = Gauge("check_failure_latest","最新巡检失败次数")
check_warning_latest = Gauge("check_warning_latest","最新巡检警告次数")
check_last_duration_seconds = Gauge("check_last_duration_seconds","最新巡检运行时间")
service_start_time = Gauge("service_start_time","服务启动时间")



# 服务启动检查项，yield前的是启动前运行的代码，yield后面的是终止服务的最后运行代码
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    服务启动检查
    """
    ssh_vmware.get_conf(Path(__file__).parent / "ssh.conf")
    service_start = time.time()
    service_start_time.set(service_start)
    create_db()
    yield



app = FastAPI(lifespan=lifespan)

# 定义api对象（实例）
# app = FastAPI()

# 打开日志
ssh_vmware.setup_log()



# 全局变量
response = {}



#-----------------------------------------------------------------------------------------------------------------------------------
# API 鉴权

API_TOKEN = os.getenv("API_TOKEN")
# 设置鉴权函数
def token_verify(x_token: None|str = Header(None)) -> None:
    """

    """
    if API_TOKEN is None:
        raise HTTPException(status_code=500, detail=f"未获取到api token ")
    if x_token is None or not hmac.compare_digest(x_token, API_TOKEN):
        raise HTTPException(status_code=401, detail=f"鉴权失败")

# 设置接口，鉴权成功则触发
@app.get("/auth", dependencies=[Depends(token_verify)])
def auth_check():
    return {"detail":"验证成功"}

# API 鉴权
#-----------------------------------------------------------------------------------------------------------------------------------






# 设置参数默认值与字符类型
class CheckRequest(BaseModel):
    """
    定义post传入body的参数格式
    参数校验模型
    """
    threshold: int = 85
    workers: int = 3

def launch(workers_launch: int, threshold_launch: int) -> None:
    """
    运行检查程序
    """
    global response

    # 巡检开始时间
    start_time = time.time()


    # 获取配置文件
    try:
        hosts = ssh_vmware.get_conf(Path(__file__).parent / "ssh.conf")
    except ssh_vmware.ConfigNotFound as e:
        ssh_vmware.log.exception("配置加载失败")
        response = {
            "status": "FAILED",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            # "msg": result_list,
            "threshold": threshold_launch,
            "workers": workers_launch,
            "detail": str(e)
        }
        return

        # 执行任务获取返回值
    result_list = ssh_vmware.run_cmd_parallel(hosts,workers_launch, threshold_launch)

    response = {
        "status": "OK",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        #"msg": result_list,
        "threshold": threshold_launch,
        "workers": workers_launch,
        "success": sum(1 for result in result_list if result["status"] == "SUCCESS"),
        "warning": sum(1 for result in result_list if result["status"] == "WARNING"),
        "failure": sum(1 for result in result_list if result["status"] == "FAILURE")
    }
    end_time = time.time()

    # 运行完成之后，更新指标
    success_count = int(response["success"])
    warning_count = int(response["warning"])
    failure_count = int(response["failure"])

    # Counter
    check_runs_total.inc()
    check_success_total.inc(success_count)
    check_warning_total.inc(warning_count)
    check_failure_total.inc(failure_count)
    # Gauge
    check_success_latest.set(success_count)
    check_warning_latest.set(warning_count)
    check_failure_latest.set(failure_count)
    check_last_duration_seconds.set(end_time - start_time)



@app.post("/run",status_code=202, dependencies=[Depends(token_verify)])
def run_check(body: CheckRequest, background_tasks: BackgroundTasks) -> dict:
    """
    post 触发脚本运行
    """
    background_tasks.add_task(launch, body.workers, body.threshold)
    return {"status": "PENDING","msg": "正在运行"}

@app.get("/run/check_result", dependencies=[Depends(token_verify)])
def get_result() -> dict:
    """
    获取执行结果
    """
    if response:
        return response
    else:
        raise HTTPException(status_code=404,detail="请稍后查询")





# /merics 指标暴露
@app.get("/metrics", response_class=PlainTextResponse)
def show_metrics():
    """
    使用generate_latest() ， 直接暴露设值的指标信息
    """
    return generate_latest()










"""
python -m uvicorn ssh_cmd_fastapi:app --host 0.0.0.0 --reload

curl -X POST http://192.168.96.108:8000/run -H "Content-Type: application/json" -d'{}' -w '\n%{http_code}\n'
curl -X POST http://192.168.96.108:8000/run -H "Content-Type: application/json" -d "{\"workers\":1,\"threshold\":10}" -w '\n%{http_code}\n'
curl -X POST http://192.168.96.108:8000/run -H "Content-Type: application/json" -d "{\"workers\":\"a\",\"threshold\":10}" -w '\n%{http_code}\n'
curl -X POST http://192.168.96.108:8000/run -H "Content-Type: application/json" -d "{\"workers\":1,\"threshold\":\"b\"}" -w '\n%{http_code}\n'

curl http://192.168.96.108:8000/run/check_result -w '\n%{http_code}\n'
"""

"""
python -m uvicorn ssh_cmd_fastapi:app --host 0.0.0.0 --reload

curl.exe -X POST http://127.0.0.1:8000/run -H "Content-Type: application/json" -d'{}' -w '\n%{http_code}\n'
curl.exe -X POST http://127.0.0.1:8000/run -H "Content-Type: application/json" -d "{\"workers\":1,\"threshold\":10}" -w '\n%{http_code}\n'
curl.exe -X POST http://127.0.0.1:8000/run -H "Content-Type: application/json" -d "{\"workers\":\"a\",\"threshold\":10}" -w '\n%{http_code}\n'
curl.exe -X POST http://127.0.0.1:8000/run -H "Content-Type: application/json" -d "{\"workers\":1,\"threshold\":\"b\"}" -w '\n%{http_code}\n'

curl.exe http://127.0.0.1:8000/run/check_result -w '\n%{http_code}\n'
"""

"""
# 生成32位密码
python -c "import secrets; print(secrets.token_hex(32))"
# windows添加环境变量
$env:API_TOKEN = "6fbc6a69c8b71c99121ca41a6d9e882fdadd405ed185e01e9e9a8336e4f2fff1"
# 启动命令
python -m uvicorn ssh_cmd_fastapi:app --host 0.0.0.0 --reload

curl -XGET http://192.168.96.108:8000/auth -H "x-token:6fbc6a69c8b71c99121ca41a6d9e882fdadd405ed185e01e9e9a8336e4f2fff1"

"""

