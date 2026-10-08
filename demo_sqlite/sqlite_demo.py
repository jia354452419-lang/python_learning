"""
3.6 SQLite 教学版：巡检报告落库
知识点：建表、参数化插入、查询、上下文管理器、防 SQL 注入、row_factory

运行：python sqlite_demo.py
"""
import sqlite3
from pathlib import Path
from datetime import datetime

# 数据库文件放脚本同目录（单文件，零运维）
DB_PATH = Path(__file__).parent / "inspect.db"


def init_db():
    """建表（幂等：IF NOT EXISTS 重复执行不报错）"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                threshold INTEGER,
                workers INTEGER,
                success INTEGER,
                warning INTEGER,
                failure INTEGER
            )
        """)


def save_report(status, threshold, workers, success, warning, failure):
    """插入一条巡检报告（参数化查询防注入）"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO reports 
               (timestamp, status, threshold, workers, success, warning, failure)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             status, threshold, workers, success, warning, failure)
        )


def get_latest_report():
    """查最新一条报告（row_factory 让返回值能用列名访问）"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row  # 返回 dict-like 对象而非 tuple
        cursor = conn.execute(
            "SELECT * FROM reports ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_history(limit=10):
    """查最近 N 条报告"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM reports ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]


def get_reports_by_status(status):
    """按状态查询（演示 WHERE 条件）"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM reports WHERE status=? ORDER BY id DESC", (status,)
        )
        return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    # 1. 建表
    init_db()
    print("[OK] 建表完成")

    # 2. 插入 3 条测试数据
    save_report("OK", 85, 3, 10, 2, 1)
    save_report("FAILED", 85, 3, 0, 0, 5)
    save_report("OK", 90, 5, 15, 1, 0)
    print("[OK] 插入 3 条报告")

    # 3. 查最新
    latest = get_latest_report()
    print(f"\n最新报告：{latest}")

    # 4. 查历史
    history = get_history(limit=5)
    print(f"\n最近 {len(history)} 条：")
    for r in history:
        print(f"  id={r['id']} {r['timestamp']} {r['status']} 成功={r['success']}")

    # 5. 按状态查
    failed = get_reports_by_status("FAILED")
    print(f"\nFAILED 报告共 {len(failed)} 条")

    # 6. 演示 SQL 注入（危险，仅教学）
    print("\n--- SQL 注入演示（为什么必须用参数化） ---")
    malicious_input = "' OR '1'='1"
    with sqlite3.connect(DB_PATH) as conn:
        # [危险] 错误姿势：f-string 拼接（会查出所有记录）
        cursor = conn.execute(f"SELECT * FROM reports WHERE status='{malicious_input}'")
        print(f"[危险] f-string 拼接查到 {len(cursor.fetchall())} 条（注入成功，泄露全表）")

        # [安全] 正确姿势：参数化查询（查不到，安全）
        cursor = conn.execute("SELECT * FROM reports WHERE status=?", (malicious_input,))
        print(f"[安全] 参数化查询查到 {len(cursor.fetchall())} 条（注入失败，安全）")
