"""
阶段 2 教学版：巡检工具服务化（项目 2 第四期）
POST /check/run    触发一次巡检（后台执行，立即返回回执）
GET  /check/report 查最近一次巡检报告

启动：python -m uvicorn check_api:app --port 8000
验证：
    curl -X POST http://192.168.96.108:8000/check/run -H "Content-Type: application/json" -d "{\"threshold\": 90}"
    curl http://192.168.96.108:8000/check/report        ← 立刻查：还没跑完
    curl http://192.168.96.108:8000/check/report        ← 10 秒后再查：报告出来了
"""
import time
from datetime import datetime

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# 最近一次报告（教学简化：存内存。生产会落盘/数据库，重启不丢）
LAST_REPORT = None


class CheckRequest(BaseModel):
    """请求体的类型注解：阶段 1 的标量注解 → 这里是整个 JSON body。

    POST body {"threshold": 90} 会被 Pydantic 自动解析成 CheckRequest 对象；
    threshold 不是 int（比如传 "abc"）→ 422，进不了函数。
    """
    threshold: int = 85          # 带默认值：body 传 {} 也合法


def run_check(threshold: int):
    """模拟巡检：真实版这里是 csv_file/ssh_vmware.py 的 run_cmd_parallel。"""
    global LAST_REPORT
    time.sleep(10)               # 模拟几十台主机的 SSH 耗时
    LAST_REPORT = {
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "threshold": threshold,
        "summary": {"total": 3, "ok": 2, "warn": 1},
    }


@app.post("/check/run", status_code=202)   # 202 Accepted = 收到了，但还没处理完
def check_run(req: CheckRequest, background_tasks: BackgroundTasks):
    # 为什么不能同步跑完再返回：巡检几十台要几十秒，客户端（curl/前端/网关）
    # 会超时干等。模式 = 立即回执 + 后台干活 + 轮询查结果
    # —— 和你在项目 1 里"触发 Jenkins 构建"是同一模式
    background_tasks.add_task(run_check, req.threshold)
    return {"msg": "巡检已触发", "threshold": req.threshold}


@app.get("/check/report")
def check_report():
    if LAST_REPORT is None:
        raise HTTPException(status_code=404, detail="还没有报告，先 POST /check/run")
    return LAST_REPORT
