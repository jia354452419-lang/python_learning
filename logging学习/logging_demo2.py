"""
logging 第二课：Handler —— 决定日志"去哪"

basicConfig 的局限：一旦写了 filename 参数，日志就只进文件、不上屏幕，
做不到"一边 print 一边写文件"。想多路输出，就得显式创建 Handler。

本课复刻你手写 log() 的能力（屏幕 + 文件），并解锁它没有的能力：
两路输出可以有不同的门槛、不同的格式。
"""

import logging

# ---- 1. Logger：和第一课一样拿对象 ----
log = logging.getLogger("host_check")
log.setLevel(logging.DEBUG)          # Logger 总门槛：DEBUG 全放行

# ---- 2. Handler ①：控制台 ----
console = logging.StreamHandler()    # 输出到屏幕（stderr）
console.setLevel(logging.INFO)       # 控制台自己的门槛：INFO 及以上
console.setFormatter(
    logging.Formatter('%(levelname)-7s | %(message)s')          # 屏幕格式：简短
)

# ---- 3. Handler ②：文件 ----
file_h = logging.FileHandler('demo2.log', encoding='utf-8')     # append 模式，句柄常驻
file_h.setLevel(logging.DEBUG)      # 文件自己的门槛：全记
file_h.setFormatter(
    logging.Formatter('%(asctime)s | %(levelname)-7s | %(message)s')  # 文件格式：带时间
)

# ---- 4. 挂载：一个 Logger 挂两个 Handler，一条日志同时去两地 ----
log.addHandler(console)
log.addHandler(file_h)

# ---- 5. 测试 ----
log.debug("我只能在文件里看到（被控制台的 INFO 门槛拦下了）")
log.info("屏幕和文件都有我")
log.warning("丢包率 > 50% 的那种告警")
log.error("ping 不通的那种告警")
