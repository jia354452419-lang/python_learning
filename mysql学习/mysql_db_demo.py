"""3.8 MySQL 存储进阶·教学版
对照 ssh_cmd_sqlite_4/ssh_cmd_db.py：同样四个函数，看 SQLite→MySQL 的迁移差异。

运行前置：
  1. 一台 MySQL 实例（测试机 / docker 均可，例如：
     docker run -d --name mysql38 -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root123 \
         -v mysql38_data:/var/lib/mysql mysql:8   ）
  2. 连接信息走环境变量（密码不进代码，安全红线——与第三期删密码同源）：
     $env:MYSQL_HOST='192.168.102.x'; $env:MYSQL_PASSWORD='xxx'
  3. python mysql_db_demo.py
"""

import logging
import os
from contextlib import closing
from datetime import datetime, timezone

import pymysql
import pymysql.cursors

logger = logging.getLogger(__name__)

# env 进程级不变，import 时快照一次即可（12-factor；不涉及 #50 的配置快照坑）
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'charset': 'utf8mb4',   # MySQL 的 utf8 是残血三字节，utf8mb4 才是完整 UTF-8
}
DATABASE = os.getenv('MYSQL_DB', 'ops_learning')


def get_conn(database=None):
    """新建一条连接 = TCP 握手 + 认证（sqlite3.connect 只是打开文件，完全两回事）。
    database=None：连实例但不选库——建库本身需要这种连接。"""
    cfg = dict(DB_CONFIG)
    if database:
        cfg['database'] = database
    return pymysql.connect(**cfg)


def create_database():
    """MySQL 连接要求库已存在（sqlite 是文件不存在自动建，正好相反）。
    类比：mysql -e "CREATE DATABASE IF NOT EXISTS ..." """
    with closing(get_conn()) as conn:
        with conn.cursor() as cur:
            # 库名/表名是"标识符"不是"值"，%s 参数化替不了——来源限定环境变量（可信），不能用用户输入
            cur.execute(f'CREATE DATABASE IF NOT EXISTS {DATABASE} '
                        f'DEFAULT CHARACTER SET utf8mb4')
        conn.commit()


def create_table():
    with closing(get_conn(DATABASE)) as conn:
        with conn.cursor() as cur:
            # 类型从严：sqlite 万物 TEXT（#55 字典序坑的温床）→ MySQL 强类型
            # 短串 VARCHAR(n)、长文 TEXT、数字 INT、时间 DATETIME
            cur.execute('''CREATE TABLE IF NOT EXISTS ssh_cmd (
                ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                GROUPID VARCHAR(14) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                ip VARCHAR(45) NOT NULL,
                port INT NOT NULL,
                status VARCHAR(10) NOT NULL,
                use_percent INT NOT NULL,
                detail TEXT NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        conn.commit()   # DDL 在 MySQL 隐式提交，这行只是保持模式统一


def insert_newline(groupid, created_at, ip, port, status, use_percent, detail):
    # closing 补 close：PyMySQL 的 with conn 只管 commit/rollback，不管关连接！
    with closing(get_conn(DATABASE)) as conn:
        with conn.cursor() as cur:
            # 占位符方言：sqlite 用 ?，PyMySQL 用 %s——它不是 % 字符串格式化！
            # 所有类型（int/datetime 也一样）一律 %s，驱动负责转义，是参数化查询（防注入）
            cur.execute('''INSERT INTO ssh_cmd
                (GROUPID, created_at, ip, port, status, use_percent, detail)
                VALUES (%s,%s,%s,%s,%s,%s,%s)''',
                        (groupid, created_at, ip, port, status, use_percent, detail))
        conn.commit()   # MySQL 默认手动提交：忘 commit = 连接一关就回滚（沉默丢数据，#18 同族）


def query_data_latest():
    with closing(get_conn(DATABASE)) as conn:
        # DictCursor：fetchall 直接给 [dict,...]，替代 sqlite 的 row_factory + dict(i)
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute('SELECT * FROM ssh_cmd '
                        'WHERE GROUPID = (SELECT MAX(GROUPID) FROM ssh_cmd)')
            return cur.fetchall()


def query_data_status(status):
    with closing(get_conn(DATABASE)) as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute('SELECT * FROM ssh_cmd WHERE status = %s', (status,))
            return cur.fetchall()


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')
    create_database()
    create_table()
    # DATETIME 无时区：存 UTC 朴素时间（#66 哲学：存储一律 UTC，换算只在展示边缘）
    # PyMySQL 自动把 datetime 对象转成 SQL 字面量，不用自己 strftime
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    insert_newline(now.strftime('%Y%m%d%H%M%S'), now,
                   '192.0.2.1', 22, 'SUCCESS', 30, '教学版自测行')
    logger.info('最新一批: %s', query_data_latest())
    logger.info('SUCCESS 行: %s', query_data_status('SUCCESS'))


if __name__ == '__main__':
    main()
