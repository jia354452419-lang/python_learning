"""
对照实验：when='midnight' 对"短命脚本"是否有效？

原理：midnight 分支在构造 handler 时会先看日志文件的 mtime（最后修改时间），
 rol转点 = "mtime 所在那天的下一个午夜"。文件 mtime 是昨天 → 轮转点=今天 00:00
 → 早已过期 → 第一条写入立即触发轮转。

本实验用 os.utime 把文件 mtime 伪造成昨天，模拟"跨天后再跑"。
"""

import os
import time
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# 造一个已存在的日志文件，mtime 伪造成昨天
open('demo_mid.log', 'w', encoding='utf-8').close()
yesterday = time.time() - 86400
os.utime('demo_mid.log', (yesterday, yesterday))

log = logging.getLogger("demo_mid")
log.setLevel(logging.INFO)   # 上一个 demo 的教训，这次不忘

h = TimedRotatingFileHandler('demo_mid.log', when='midnight', backupCount=5, encoding='utf-8')
log.addHandler(h)

print(f"现在时刻 = {datetime.now():%Y-%m-%d %H:%M:%S}")
print(f"轮转点   = {datetime.fromtimestamp(h.rolloverAt):%Y-%m-%d %H:%M:%S}（早已过期！）")

log.info("第一条写入 → 应立即触发轮转")
print("目录:", sorted(f for f in os.listdir('.') if f.startswith('demo_mid')))
