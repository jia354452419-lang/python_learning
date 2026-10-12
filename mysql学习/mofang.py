import os
import pymysql
from datetime import datetime
from contextlib import closing

from networkx.algorithms.centrality import group

DB_INFO = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "port": int(os.getenv("MYSQL_PORT")),
}
DB_NAME = os.getenv("MYSQL_DATABASE","mofang_db")


def connect_mysql(database=None):
    info = dict(DB_INFO)
    if database:
        DB_INFO["database"] = DB_NAME
        info = dict(DB_INFO)
    return pymysql.connect(**info)

def craete_db():
    with closing(connect_mysql()) as conn:
        with conn.cursor() as cur:
            cur.execute(f'''CREATE DATABASE IF NOT EXISTS {DB_NAME};''')
        conn.commit()

def create_tables():
    with closing(connect_mysql(DB_NAME)) as conn:
        with conn.cursor() as cur:
            cur.execute(f'''CREATE TABLE IF NOT EXISTS pods_status (
                            ID INT NOT NULL AUTO_INCREMENT,
                            group_id VARCHAR(15) DEFAULT NULL,
                            create_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            ip VARCHAR(45) DEFAULT NULL,
                            port INT DEFAULT NULL,
                            status VARCHAR(15) DEFAULT NULL,
                            use_percent INT DEFAULT NULL,
                            detail TEXT DEFAULT NULL,
                        ''')
        conn.commit()
        
def insert_row(group_id,create_at,ip,port,status,use_percent,detail):
    with closing(connect_mysql(DB_NAME)) as conn:
        with conn.cursor() as cur:
            cur.execute(f'''INSERT INTO pods_status (group_id,create_at,ip,port,status,use_percent,detail) VALUES (%s,%s,%s,%s,%s,%s)''',(group_id,create_at,ip,port,status,use_percent,detail))
        conn.commit()

def query_latest():
    with closing(connect_mysql(DB_NAME)) as conn:
        with conn.cursor() as cur:
            cur.execute(f'''SELECT * FROM pods_status WHERE group_id == MAX(group_id)''')
        conn.commit()

def query_status(status):
    with closing(connect_mysql(DB_NAME)) as conn:
        with conn.cursor() as cur:
            cur.execute(f'''SELECT * FROM pods_status WHERE status == %s''',(status,))





def main():

    # 数据库连接函数
    # 创建数据库
    # 创建表
    # 插入数据
    # 查询最新groupid数据
    # 按状态查询数据

    pass