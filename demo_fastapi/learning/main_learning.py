
from fastapi import FastAPI, HTTPException

HOSTS = {
    "192.168.102.11": {"hostname": "web01", "env": "prod"},
    "192.168.102.12": {"hostname": "db01", "env": "prod"},
    "192.168.102.13": {"hostname": "test01", "env": "test"},
}

learning = FastAPI()

@learning.get("/")
def home():
    return {"hello": "world"}

@learning.get("/health")
def health():
    return {"status": "ok"}

@learning.get("/hosts")
def hosts():
    return {"total": len(HOSTS), "hosts": HOSTS}

@learning.get("/hosts/{ip}")
def get_host(ip: str):
    if ip in HOSTS:
        return {"ip": ip, **HOSTS[ip]}
    else:
        raise HTTPException(status_code=404, detail=f"HOST {ip} Not Found")