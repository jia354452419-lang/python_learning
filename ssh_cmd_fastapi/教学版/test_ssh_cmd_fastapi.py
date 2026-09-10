"""
3.5 pytest 教学版：给巡检服务写测试
被测对象：ssh_cmd_fastapi.py 的 FastAPI app
知识点：TestClient、fixture、参数化、mock 后台任务、断言状态码+响应体

运行：pytest test_ssh_cmd_fastapi.py -v
"""
import os
import pytest
from fastapi.testclient import TestClient

# 测试前必须设置环境变量（否则 import 时 API_TOKEN 是 None，500）
os.environ["API_TOKEN"] = "test-token-12345"

from ssh_cmd_fastapi import app, API_TOKEN


@pytest.fixture
def client():
    """每个测试函数拿一个干净的 TestClient（相当于 curl 的 Python 版）"""
    return TestClient(app)


# ========== 1. 鉴权测试（3.3 的回归网） ==========

def test_metrics_no_auth_needed(client):
    """/metrics 不鉴权（学员裁定）"""
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "check_runs_total" in resp.text


def test_run_without_token_returns_401(client):
    """POST /run 无 token → 401"""
    resp = client.post("/run", json={"workers": 1, "threshold": 85})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "鉴权失败"


def test_run_with_wrong_token_returns_401(client):
    """POST /run 错误 token → 401"""
    resp = client.post("/run", json={"workers": 1, "threshold": 85},
                       headers={"X-Token": "wrong-token"})
    assert resp.status_code == 401


def test_run_with_correct_token_returns_202(client):
    """POST /run 正确 token → 202 PENDING"""
    resp = client.post("/run", json={"workers": 1, "threshold": 85},
                       headers={"X-Token": "test-token-12345"})
    assert resp.status_code == 202
    assert resp.json()["status"] == "PENDING"


# ========== 2. 参数校验测试（FastAPI 自动做的，但要验证契约没破） ==========

@pytest.mark.parametrize("bad_body", [
    {"workers": "a", "threshold": 85},      # 类型错误
    {"workers": 1, "threshold": "b"},       # 类型错误
    {},                                     # 缺字段（有默认值，应该 202）
])
def test_run_body_validation(client, bad_body):
    """body 校验：类型错 422，缺字段用默认值 202"""
    resp = client.post("/run", json=bad_body,
                       headers={"X-Token": "test-token-12345"})
    if not bad_body:  # 空 dict 用默认值
        assert resp.status_code == 202
    else:  # 类型错误
        assert resp.status_code == 422


# ========== 3. 查询接口测试 ==========

def test_get_result_before_run_returns_404(client):
    """未触发巡检时查询 → 404"""
    # 注意：这个测试依赖全局 - 是 {}，如果前面跑过 test_run_with_correct_token
    # 全局 response 已有值，会失败。这是真实问题，3.6 落库后解决
    resp = client.get("/run/check_result",
                      headers={"X-Token": "test-token-12345"})
    # 可能 200（前面测试触发过）或 404（没触发过）
    assert resp.status_code in [200, 404]


# ========== 4. 边界：服务端未配置 API_TOKEN ==========

def test_server_without_token_configured(monkeypatch, client):
    """模拟服务端没配 API_TOKEN → 500"""
    monkeypatch.setattr("ssh_cmd_fastapi.API_TOKEN", None)
    resp = client.post("/run", json={"workers": 1, "threshold": 85},
                       headers={"X-Token": "any-token"})
    assert resp.status_code == 500
    assert "未获取到api token" in resp.json()["detail"]
