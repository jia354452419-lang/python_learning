

import ssh_vmware
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime


# 定义api对象（实例）
app = FastAPI()

# 打开日志
ssh_vmware.setup_log()



# 全局变量
response = {}

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
    # 获取配置文件
    hosts = ssh_vmware.get_conf(Path(__file__).parent / "ssh.conf")
    # 执行任务获取返回值
    result_list = ssh_vmware.run_cmd_parallel(hosts,workers_launch, threshold_launch)

    global response

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


@app.post("/run",status_code=202)
def run_check(body: CheckRequest, background_tasks: BackgroundTasks) -> dict:
    """
    post 触发脚本运行
    """
    background_tasks.add_task(launch, body.workers, body.threshold)
    return {"status": "PENDING","msg": "正在运行"}

@app.get("/run/check_result")
def get_result() -> dict:
    """
    获取执行结果
    """
    if response:
        return response
    else:
        raise HTTPException(status_code=404,detail="请稍后查询")


"""
curl -X POST http://192.168.96.108:8000/run -H "Content-Type: application/json" -d'{}' -w '\n%{http_code}\n'
curl -X POST http://192.168.96.108:8000/run -H "Content-Type: application/json" -d "{\"workers\":1,\"threshold\":10}" -w '\n%{http_code}\n'
curl -X POST http://192.168.96.108:8000/run -H "Content-Type: application/json" -d "{\"workers\":\"a\",\"threshold\":10}" -w '\n%{http_code}\n'
curl -X POST http://192.168.96.108:8000/run -H "Content-Type: application/json" -d "{\"workers\":1,\"threshold\":\"b\"}" -w '\n%{http_code}\n'

curl http://192.168.96.108:8000/run/check_result -w '\n%{http_code}\n'
"""

