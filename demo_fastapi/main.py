"""
阶段 1 教学版：第一个 FastAPI 服务
三个接口：GET /health  GET /hosts  GET /hosts/{ip}

启动（在本文件所在目录）：
    .venv/Scripts/python -m uvicorn main:app --reload
验证：
    curl http://127.0.0.1:8000/health
    curl http://127.0.0.1:8000/hosts
    curl http://127.0.0.1:8000/hosts/192.168.102.11
    curl http://127.0.0.1:8000/hosts/1.2.3.4        ← 触发业务 404
    浏览器打开 http://127.0.0.1:8000/docs            ← 自动接口文档
"""
from fastapi import FastAPI, HTTPException

# 应用对象：所有路由都注册到它身上，uvicorn 启动时找的就是它
app = FastAPI()

# 模拟数据：就当是从 ssh.conf 读出来的主机清单（阶段 2 再接真配置）
HOSTS = {
    "192.168.102.11": {"hostname": "web01", "env": "prod"},
    "192.168.102.12": {"hostname": "db01", "env": "prod"},
    "192.168.102.13": {"hostname": "test01", "env": "test"},
}


@app.get("/health")                      # 装饰器 ≈ nginx 的 location /health {}：
def health():                            # 把 URL 路径和处理函数绑定起来
    return {"status": "ok"}              # 返回 dict，框架自动 json.dumps
                                         # + 自动带 Content-Type: application/json


@app.get("/hosts")
def list_hosts():
    return {"total": len(HOSTS), "hosts": HOSTS}


@app.get("/hosts/{ip}")                  # {ip} 是路径参数，名字必须和下面形参一致
def get_host(ip: str):                   # ip: str 类型注解是 FastAPI 的饭碗：
                                         # 校验、类型转换、/docs 文档全靠它
    if ip not in HOSTS:
        # 业务 404：路径匹配上了，但资源不存在 → 自己抛
        # （路径根本没匹配的 404 框架自动管，不用你写）
        raise HTTPException(status_code=404, detail=f"host {ip} not found")
    return {"ip": ip, **HOSTS[ip]}
