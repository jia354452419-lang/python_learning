"""
logging 第一课：最小可运行例子

和手写 log() 的对照：
    log(f"info | name: ...")   →  log.info(f"name: ...")   # 级别从"拼字符串"变成"方法名"
    手拼时间戳                   →  %(asctime)s             # Formatter 接管
    print 到屏幕                →  默认 Handler             # 输出到控制台
"""

import logging

# ---- 1. 一次性全局配置 ----
logging.basicConfig(
    level=logging.WARNING,                                   # 门槛：低于这个级别的日志，直接丢弃
    format='%(asctime)s | %(levelname)-10s | %(message)s',  # 时间 | 级别 | 内容
)

# ---- 2. 拿一个记录器（Logger）----
# 名字随便起；名字相同，拿到的永远是同一个 Logger 对象
log = logging.getLogger("host_check")

# ---- 3. 按级别记录（级别是方法名，不再是拼进消息的装饰）----
log.debug("DEBUG：最详细的调试信息，排查问题时才打开")
log.info("INFO：正常运行信息，对应你现在的 info")
log.warning("WARNING：异常苗头，对应你的丢包率>50% WARN")
log.error("ERROR：出错了，对应你的 ping 不通")
log.critical("CRITICAL：整个程序要完，暂时用不上")
