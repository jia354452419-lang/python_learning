"""
logging 第三课：TimedRotatingFileHandler —— 按时间自动轮转日志

你手写版的方案：拼日期文件名 host_check_2026-08-31.log，每天一个新文件。
logging 的方案：文件名固定 host_check.log，到点后把旧文件改名加时间后缀，
再开一个新文件继续写。这就是运维的老熟人 logrotate 的思路。

本课先用 when='S'（每秒轮转）做演示，方便肉眼看到切割效果；
生产环境用 when='midnight'（每天午夜切割）。
"""

import logging
from logging.handlers import TimedRotatingFileHandler

log = logging.getLogger("host_check.rotate")
log.setLevel(logging.DEBUG)

# ---- 轮转式文件 Handler ----
file_h = TimedRotatingFileHandler(
    'demo3.log',            # 当前日志永远叫这个名字（不带日期！）
    when='S',               # 'S'秒 / 'M'分 / 'H'时 / 'D'天 / 'midnight'每天午夜
    backupCount=7,          # 旧日志最多留 7 份，更老的自动删除（logrotate 的 rotate 7）
    encoding='utf-8',
)
file_h.setFormatter(
    logging.Formatter('%(asctime)s | %(levelname)-7s | %(message)s')
)
log.addHandler(file_h)

log.info("写入一条")
log.warning("再写一条")
