"""
阶段 3.3 教学版：Token 鉴权
知识点：Header 传凭证、Depends 依赖注入、401 语义、环境变量存密钥、hmac.compare_digest

启动：set API_TOKEN=test123 后  python -m uvicorn auth_demo:app --port 8010
生成强 token：python -c "import secrets; print(secrets.token_hex(32))"
"""
import hmac
import os

from fastapi import FastAPI, Depends, Header, HTTPException

# 启动时从环境变量读一次（密钥不进代码 —— 安全红线，与第三期删密码字段同源裁定）
API_TOKEN = os.environ.get("API_TOKEN")

app = FastAPI()


def verify_token(x_token: str | None = Header(None)) -> None:
    """
    鉴权依赖：用 dependencies=[Depends(verify_token)] 挂到路由上。
    类比 nginx auth_request / 机房门禁：凭证不过，业务函数体根本不执行。
    FastAPI 自动把形参 x_token 映射到请求头 X-Token（下划线自动转连字符）。
    Header(None) = 允许不带该头，不带时给 None，由我们统一判 401。
    """
    if API_TOKEN is None:
        # 服务端自己没配密钥 → 服务坏了，不是客户端的错 → 500
        raise HTTPException(status_code=500, detail="服务端未配置 API_TOKEN")
    if x_token is None or not hmac.compare_digest(x_token, API_TOKEN):
        # 没带凭证 / 凭证错误统一 401，detail 不区分（不给攻击者提示）
        # compare_digest：恒定时间比较，防逐位时序爆破；== 会逐字符短路泄露时间差
        raise HTTPException(status_code=401, detail="无效token")


@app.get("/public")
def public() -> dict:
    """开放接口：任何人可访问（对照：/docs、/health 这类）"""
    return {"msg": "公开信息，谁都能看"}


@app.get("/private", dependencies=[Depends(verify_token)])
def private() -> dict:
    """受保护接口：verify_token 放行后函数体才执行（对照：/run/check_result）"""
    return {"msg": "凭证有效，机密信息给你"}


@app.post("/danger", dependencies=[Depends(verify_token)])
def danger() -> dict:
    """写操作更要保护（对照：POST /run 触发巡检）"""
    return {"msg": "危险操作已执行"}



#  $env:API_TOKEN = "6fbc6a69c8b71c99121ca41a6d9e882fdadd405ed185e01e9e9a8336e4f2fff1"
#  python -m uvicorn auth_demo:app
#  curl.exe -XGET http://127.0.0.1:8000/private -H "x-token:6fbc6a69c8b71c99121ca41a6d9e882fdadd405ed185e01e9e9a8336e4f2fff1"
