import hmac
import os
import time
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from contextlib import asynccontextmanager
from typing import Literal
from pathlib import Path

# 引入prometheus模块
from prometheus_client import Counter,Gauge,generate_latest
# 引入主程序模块
from container_status import pods_status, containers_status, replica_deployment_status, get_k8s_config, set_up_log
# 引入数据库模块
from container_status_db import create_db_pods_status, query_pods_status, query_by_status, query_by_time


# Guage
service_start_time = Gauge("service_start_time","服务启动时间")





# 创建fastapi对象
@asynccontextmanager
async def lifespan(app: FastAPI):
    get_k8s_config()
    create_db_pods_status()
    set_up_log()
    service_start_time.set(time.time())
    yield

app = FastAPI(lifespan=lifespan)


# 设置Token鉴权函数
TOKEN_KEY = os.getenv("TOKEN_KEY")
def token_verify(token_key: None|str =Header(None)):
    if TOKEN_KEY is None:
        raise HTTPException(status_code=500,detail="无法获取Token Key")
    if token_key is None or not hmac.compare_digest(token_key,TOKEN_KEY):
        raise HTTPException(status_code=401,detail="Token Key is wrong")
# $env:TOKEN_KEY = "123"



# 触发查询
@app.post("/run/pods_status",status_code=200,dependencies=[Depends(token_verify)])
def run_query_pods_status():
    return pods_status()

@app.post("/run/containers_status",status_code=200,dependencies=[Depends(token_verify)])
def run_query_containers_status():
    return containers_status()

@app.post("/run/replica_deployment_status",status_code=200,dependencies=[Depends(token_verify)])
def run_query_replica_deployment_status():
    return replica_deployment_status()

# 按pod查询数据
@app.get("/query/pods_status",status_code=200,dependencies=[Depends(token_verify)])
def query_one(name):
    return query_pods_status(name)

# 按时间查询数据
@app.get("/query/time",status_code=200,dependencies=[Depends(token_verify)])
def query_two(start_time,end_time):
    return query_by_time(start_time,end_time)

# 按状态查询数据
@app.get("/query/summarize",status_code=200,dependencies=[Depends(token_verify)])
def query_summarize(summarize: Literal["OK","ERROR"]):
    return query_by_status(summarize)


# 暴露指标
@app.get("/metrics",response_class=PlainTextResponse)
def metrics():
    return generate_latest()

# 前端巡检台（教练交付）：单文件页面，数据仍走上面的鉴权 API
@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(Path(__file__).parent / "dashboard.html")


"""
 触发功能函数
curl -X POST http://192.168.96.108:8000/run/pods_status -H 'token-key:123' | jq '.[].summarize'
curl -X POST http://192.168.96.108:8000/run/containers_status -H 'token-key:123' | jq '.[].summarize'
curl -X POST http://192.168.96.108:8000/run/replica_deployment_status -H 'token-key:123' | jq '.[].summarize'

 触发查询函数 1. /query/pods_status
curl -X GET 'http://192.168.96.108:8000/query/pods_status?name=deploy-replica-mismatch-68954bf465-bbw5m' -H 'token-key:123' | jq '.[].STATUS'

curl -X GET 'http://192.168.96.108:8000/query/pods_status?name=multi-container-demo' -H 'token-key:123' | jq

curl -X GET 'http://192.168.96.108:8000/query/pods_status?name=deploy-replica-mismatch' -H 'token-key:123' | jq

 触发查询函数 2. /query/time
curl -X GET 'http://192.168.96.108:8000/query/time?start_time=2026-09-21%2011:10:43&end_time=2026-09-21%2011:15:43' -H 'token-key:123' | jq
curl -X GET 'http://192.168.96.108:8000/query/time?start_time=2026-09-21%2011:15:59&end_time=2026-09-21%2011:20:43' -H 'token-key:123' | jq

触发查询函数 3. /query/summarize
curl -X GET 'http://192.168.96.108:8000/query/summarize?summarize=OK' -H 'token-key:123' | jq
curl -X GET 'http://192.168.96.108:8000/query/summarize?summarize=ERROR' -H 'token-key:123' | jq



"""