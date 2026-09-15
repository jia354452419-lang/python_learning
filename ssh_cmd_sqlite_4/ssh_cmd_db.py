import sqlite3

from pathlib import Path


DB_NAME = Path(__file__).parent / 'ssh_cmd.db'


def create_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS ssh_cmd (
                            ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                            GROUPID TEXT NOT NULL,
                            created_at TEXT NOT NULL,
                            ip TEXT NOT NULL,
                            port TEXT NOT NULL,
                            status TEXT NOT NULL,
                            use_percent TEXT NOT NULL,
                            detail TEXT NOT NULL
                        )
                ''')

# 插入新行
def insert_newline(groupid, created_at, ip, port, status, use_percent, detail):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''INSERT INTO ssh_cmd (GROUPID, created_at, ip, port, status, use_percent, detail)
                            VALUES (?,?,?,?,?,?,?)''',
                     (groupid, created_at, ip, port, status, use_percent, detail))


# 按最新groupid查询
def query_data_latest():
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        res = conn.execute('''SELECT * FROM ssh_cmd WHERE GROUPID = (SELECT MAX(GROUPID) FROM ssh_cmd)''')
        return [dict(i) for i in res.fetchall()]

# 按状态查询
def query_data_status(status):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        res = conn.execute("""SELECT * FROM ssh_cmd WHERE STATUS = ?""",(status,))
        return [dict(i) for i in res.fetchall()]







def main():
    # 1 创建数据库、创建表
    # 2 插入数据
    # 3 查询数据 -- 很多种方式

    pass
