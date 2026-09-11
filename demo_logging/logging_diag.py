"""
轮转机制诊断：rolloverAt 到底是什么时间点？

要回答的问题：when='M' 的轮转点是
  A) 每个自然整分钟（xx:00）   —— 很多人以为的
  B) handler 创建时刻 + 60 秒   —— 相对时间，重启就重置
"""

import os
import time
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

log = logging.getLogger("demo_m2")
log.setLevel(logging.INFO)   # 教训：不设这个，info 会被默认 WARNING 门槛静默吞掉

h = TimedRotatingFileHandler('demo_m2.log', when='M', backupCount=5, encoding='utf-8')
h.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
log.addHandler(h)

# ---- 诊断 1：轮转点是什么 ----
now = time.time()
r_at = h.rolloverAt
print(f"现在时刻     = {datetime.fromtimestamp(now):%H:%M:%S}")
print(f"轮转点       = {datetime.fromtimestamp(r_at):%H:%M:%S}")
print(f"距轮转点还有 = {r_at - now:.1f} 秒")
print(f"(如果距离恰好约 60 秒 → B：从创建时刻起算 60 秒)")
print(f"(如果轮转点落在 xx:00 整 → A：自然分钟边界)")

# ---- 诊断 2：写入第一条 ----
log.info("第一条")
print("第一条写入后目录:", sorted(f for f in os.listdir('.') if f.startswith('demo_m2')))

# ---- 诊断 3：睡到轮转点之后再写一条，看轮转 ----
wait = r_at - time.time() + 1
print(f"睡 {max(wait,1):.0f} 秒，跨过轮转点...")
time.sleep(max(wait, 1))

log.info("第二条（跨过轮转点后写入）")
print("第二条写入后目录:", sorted(f for f in os.listdir('.') if f.startswith('demo_m2')))
