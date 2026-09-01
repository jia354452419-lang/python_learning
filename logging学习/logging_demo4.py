"""
logging 演示 4：轮转的真实触发时机

关键机制：TimedRotatingFileHandler 没有任何定时器/后台线程。
每次写日志时才检查："当前时间是否已经跨过了上一个轮转边界？"
  - 没跨过 → 追加到当前文件（你观察到的"总是追加"）
  - 跨过了 → 把旧文件改名归档 + 新建文件，再写入

when='M' 的边界是每个整分钟（xx:00）。本演示故意睡到跨过整分钟，
在同一次运行里亲眼看到轮转发生。
"""

import time
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

log = logging.getLogger("demo_m")

h = TimedRotatingFileHandler('demo_m.log', when='M', backupCount=5, encoding='utf-8')
h.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
log.addHandler(h)

# 第一条：写在当前分钟内
log.info(f"第一条，时刻 {datetime.now().strftime('%H:%M:%S')}")

# 睡到跨过下一个整分钟（xx:00）
now = datetime.now()
wait = 60 - now.second + 1
print(f"等待 {wait} 秒跨过分钟边界...")
time.sleep(wait)

# 第二条：跨过边界后的第一次写入 → 触发轮转
log.info(f"第二条，时刻 {datetime.now().strftime('%H:%M:%S')}（此刻轮转发生）")
