import logging
from logging.handlers import TimedRotatingFileHandler

# 1 创建log对象
log = logging.getLogger("demo3_anbo")
log.setLevel(logging.ERROR)

# 2 创建时间滚动Handle对象
time_refresh = TimedRotatingFileHandler('demo3_anbo.log', when='S', backupCount=2, encoding='utf-8')
time_refresh.setLevel(logging.WARNING)
time_refresh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 3 添加Handle到log对象
log.addHandler(time_refresh)

log.debug('111')
log.info('222')
log.warning('333')
log.error('444')
log.critical('555')