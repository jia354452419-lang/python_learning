import sqlite3
from datetime import datetime
from pathlib import Path





DB_PATH = Path(__file__).parent / "sqlite3.db"

def create_table():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
                        CREATE TABLE IF NOT EXISTS t_tasks_record (
                            ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                            GROUPID TEXT NOT NULL,
                            WORKNAME TEXT NOT NULL,
                            created_at TEXT NOT NULL,
                            WORKERS INTEGER NOT NULL,
                            THRESHOLD INTEGER NOT NULL,
                            STATUS TEXT NOT NULL
                        )
                """)

def insert_task(groupid,workname,created_at,workers,threshold,status):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
                        INSERT INTO t_tasks_record (
                            GROUPID,WORKNAME,created_at,WORKERS,THRESHOLD,STATUS)
                            VALUES (?,?,?,?,?,?)
                    """,(groupid,workname,created_at,workers,threshold,status))

def quire_task_latest():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        res = conn.execute("""
                        SELECT * FROM t_tasks_record WHERE GROUPID = (select GROUPID from t_tasks_record ORDER BY GROUPID DESC limit 1)
                    """)
        return [dict(i) for i in res.fetchall()]


if __name__ == '__main__':
    # 1 创建sqlite数据文件
    create_table()
    # 2 插入数据
    insert_task(1,"langfuse01",datetime.now().strftime("%Y%m%d %H%M%S"),1,1,"SUCCESS")
    insert_task(1,"langfuse02",datetime.now().strftime("%Y%m%d %H%M%S"),2,2,"FAILURE")
    insert_task(1,"langfuse03",datetime.now().strftime("%Y%m%d %H%M%S"),3,3,"WARNING")
    insert_task(2,"langfuse01",datetime.now().strftime("%Y%m%d %H%M%S"),1,1,"SUCCESS")
    insert_task(2,"langfuse02",datetime.now().strftime("%Y%m%d %H%M%S"),2,2,"FAILURE")
    insert_task(2,"langfuse03",datetime.now().strftime("%Y%m%d %H%M%S"),3,3,"WARNING")
    insert_task(3,"langfuse01",datetime.now().strftime("%Y%m%d %H%M%S"),1,1,"SUCCESS")
    insert_task(3,"langfuse02",datetime.now().strftime("%Y%m%d %H%M%S"),2,2,"FAILURE")

    # 3 查询数据
    print("-"*50)

    datas = quire_task_latest()
    for data in datas:
        print(data)
