import os
import pymysql
from contextlib import closing



DB_INFO = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "port": int(os.getenv("MYSQL_PORT","3306")),
    "charset": "utf8mb4"
}
DB_NAME = os.getenv("MYSQL_DATABASE", "mofang_db")


def connect_mysql(database=None):
    info = dict(DB_INFO)
    if database:
        info["database"] = database
    return pymysql.connect(**info)


def create_db():
    with closing(connect_mysql()) as conn:
        with conn.cursor() as cur:
            cur.execute(f'''CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4''')
        conn.commit()


def create_tables():
    with closing(connect_mysql(DB_NAME)) as conn:
        with conn.cursor() as cur:
            cur.execute(f'''CREATE TABLE IF NOT EXISTS pods_status (
                            ID INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
                            GROUP_ID VARCHAR(30) DEFAULT NULL,
                            NAME VARCHAR(50) DEFAULT NULL,
                            CONTAINER_NAME VARCHAR(50) DEFAULT NULL,
                            SPEC VARCHAR(10) DEFAULT NULL,
                            STATUS VARCHAR(15) DEFAULT NULL,
                            SUMMARIZE TEXT DEFAULT NULL,
                            DETAIL TEXT DEFAULT NULL,
                            CHECK_TYPE  VARCHAR(20) DEFAULT NULL,
                            CREATE_TIME DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )''')
        conn.commit()

# 新增数据
def insert_pods_status(group_id, name, container_name, spec, status, summarize, detail, check_type):
    with closing(connect_mysql(DB_NAME)) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f'''INSERT INTO pods_status (GROUP_ID,NAME,CONTAINER_NAME,SPEC,STATUS,SUMMARIZE,DETAIL,CHECK_TYPE) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)''',
                (group_id, name, container_name, spec, status, summarize, detail, check_type))
        conn.commit()

# 查询最新groupid
def query_latest():
    with closing(connect_mysql(DB_NAME)) as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute('''SELECT * FROM pods_status WHERE GROUP_ID = (SELECT MAX(GROUP_ID) FROM pods_status)''')
            return cur.fetchall()
# 按状态查询
def query_status(summarize):
    with closing(connect_mysql(DB_NAME)) as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(f'''SELECT * FROM pods_status WHERE SUMMARIZE = %s''', (summarize,))
            return cur.fetchall()

# 按name查询
def query_status_name(name):
    with closing(connect_mysql(DB_NAME)) as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(f'''SELECT * FROM pods_status WHERE NAME = %s''', (name,))
            return cur.fetchall()

# 按时间范围查询
def query_status_time_range(start_time, end_time):
    with closing(connect_mysql(DB_NAME)) as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(f'''SELECT * FROM pods_status WHERE CREATE_TIME BETWEEN %s and %s''', (start_time, end_time))
            return cur.fetchall()

def main():
    # 数据库连接函数
    # 创建数据库
    # 创建表
    # 插入数据
    # 查询最新grouppid数据
    # 按状态查询数据

    pass