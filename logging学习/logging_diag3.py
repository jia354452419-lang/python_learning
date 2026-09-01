"""
实验：when='D' 连续跑多次，会不会轮转？

原理假设：D 分支的轮转点 = 文件 mtime（最后写入时刻）+ 24 小时。
每次追加都会刷新 mtime → 轮转点跟着往后挪 → 连续跑永远追不上 → 永不轮转。

用 os.utime 把 mtime 伪造成"23 小时前"和"25 小时前"两种情况对照。
"""

import os
import time
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

def make_case(name, hours_ago):
    path = f'{name}.log'
    open(path, 'w', encoding='utf-8').close()
    t = time.time() - hours_ago * 3600          # 伪造 mtime
    os.utime(path, (t, t))

    log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    h = TimedRotatingFileHandler(path, when='D', backupCount=5, encoding='utf-8')
    log.addHandler(h)

    print(f"== mtime 伪装为 {hours_ago} 小时前（模拟上次写入时间）==")
    print(f"   现在时刻 = {datetime.now():%m-%d %H:%M}")
    print(f"   轮转点   = {datetime.fromtimestamp(h.rolloverAt):%m-%d %H:%M}")

    log.info("一条测试日志")
    print(f"   写入后目录: {sorted(f for f in os.listdir('.') if f.startswith(name))}\n")

    log.removeHandler(h)
    h.close()

make_case('demo_d_23h', 23)   # 上次写入 23 小时前：还没到 24h → 预期追加
make_case('demo_d_25h', 25)   # 上次写入 25 小时前：超过 24h  → 预期轮转
