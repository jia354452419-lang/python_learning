import os
import pytest
from fastapi.testclient import TestClient


from  ssh_cmd_db import create_db, insert_newline,query_data_latest, query_data_status


# 提前注入环境变量
os.environ["API_TOKEN"] = "123456"
# 这里API_TOKEN就会变成我们上面注入的环境变量
from ssh_cmd_fastapi import app


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr("ssh_cmd_db.DB_NAME", tmp_path / "test_db")
    return TestClient(app)

@pytest.fixture
def client_with_db(client):
    create_db()
    insert_newline("2026-09-14 10:00:00", "2026-09-14_100000", "1.1.1.1", "22", "SUCCESS", "10%", "ok")
    insert_newline("2026-09-14 10:00:00", "2026-09-14_100000", "2.2.2.2", "22", "FAILURE", "error", "timeout")
    insert_newline("2026-09-14 11:00:00", "2026-09-14_110000", "3.3.3.3", "22", "SUCCESS", "20%", "ok")
    return client

# /metrics 接口
def test_metrics(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "check_runs_total" in resp.text

# /run 接口： 1 不带token
def test_run_unwith_token(client):
    resp = client.post("/run", json={})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "鉴权失败"

# /run 接口： 2 带错token
def test_run_with_wrong_token(client):
    resp = client.post("/run", json={}, headers={"x-token": "wrong_token"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "鉴权失败"

# /run 接口： 3 带正确token
def test_run_with_right_token(client):
    resp = client.post("/run", json={}, headers={"x-token": "123456"})
    assert resp.status_code == 202
    assert resp.json()["status"] == "PENDING"

# /run 接口： 4 带正确token，但是参数错误
@pytest.mark.parametrize("bad_body",[
                          {"workers": "a", "threshold": 85},
                          {"workers": 1, "threshold": "w"},
                          {} ])
def test_run_with_right_token_with_bad_body(bad_body,client):
    resp = client.post("/run", json=bad_body, headers={"x-token": "123456"})
    if bad_body:
        assert resp.status_code == 422
    else:
        assert resp.status_code == 202

# /run/check_result 接口
# def test_run_check_result(client):
#     resp = client.get("/run/check", headers={"x-token": "123456"})
#     assert resp.status_code in [ 200, 404]


# /querydata/latest 接口
def test_querydata_latest(client_with_db):
    resp = client_with_db.get("/querydata/latest", headers={"x-token": "123456"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["ip"] == "3.3.3.3"

# /querydata/status 接口
def test_querydata_status(client_with_db):
    resp = client_with_db.get("/querydata/status?status=SUCCESS", headers={"x-token": "123456"})
    assert resp.status_code == 200
    assert len(resp.json()) == 2