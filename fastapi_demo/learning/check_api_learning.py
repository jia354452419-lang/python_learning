
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

app = FastAPI()

msg = {}

class CheckBody(BaseModel):
    """
    继承BaseModel类之后，变成一个参数校验模型
    """
    lucky_num: int = 666

def run(lucky_num: int):
    """
    定义任务函数，通过api触发这个函数
    """
    time.sleep(10)
    global msg
    msg = {"lucky_num":lucky_num, "status": "OK", "time": datetime.now().isoformat(timespec='seconds')}



@app.post("/run",status_code=202)
def request_run(body_num: CheckBody, background_task: BackgroundTasks):
    """
    定义/run api接口，并且使用后台执行任务参数BackgroundTasks，提交任务为后台执行，请注意，这里仅仅是提交任务，并不等任务结束
    """
    # 使用后台执行任务参数BackgroundTasks，提交任务为后台执行，请注意，这里仅仅是提交任务，并不等任务结束
    background_task.add_task(run, body_num.lucky_num)
    # 接口返回值
    return {"status": "PENDING", "message":"please wait"}

@app.get("/run/check")
def check_lucky_num():
    if msg:
        return msg
    else:
        raise HTTPException(status_code=404, detail="还未查询到信息")