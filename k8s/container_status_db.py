import sqlite3
from pathlib import Path


DB_NAME = Path(__file__).parent / "container_status_db.db"



def create_db_pods_status():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''CREATE TABLE  IF NOT EXISTS pods_status(
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        GROUP_ID TEXT NOT NULL,
                        NAME TEXT,
                        CONTAINER_NAME,
                        SPEC TEXT,
                        STATUS TEXT,
                        SUMMARIZE TEXT,
                        DETAIL TEXT,
                        CHECK_TYPE TEXT,
                        CREATE_TIME TIMESTAMP NOT NULL DEFAULT (datetime('now','localtime')))
        ''')





# 插入数据
def insert_pods_status(group_id,name, container_name,spec, status,summarize, detail, check_type):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''INSERT INTO pods_status (GROUP_ID, NAME,CONTAINER_NAME,SPEC,STATUS,SUMMARIZE,DETAIL,CHECK_TYPE) VALUES (?,?,?,?,?,?,?,?)''',(group_id,name,container_name, spec, status,summarize,detail,check_type))


# 查询数据
# 1.按pod名称查询
def query_pods_status(name) -> list:
    """
    pods_status/containers_status
    """
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        res = conn.execute(f"""SELECT * FROM pods_status WHERE NAME = (?)""", (name,))
        return [dict(i) for i in res.fetchall()]

# 2.按时间查询
def query_by_time(start_time,end_time):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        res = conn.execute(f"""SELECT * FROM pods_status WHERE CREATE_TIME BETWEEN (?) AND (?)""", (start_time,end_time))
        return [dict(i) for i in res.fetchall()]

# 3.按状态查询
def query_by_status(summarize):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        res = conn.execute(f"""SELECT * FROM pods_status WHERE SUMMARIZE = (?)""", (summarize,))
        return [dict(i) for i in res.fetchall()]









