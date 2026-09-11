import logging

# 1 创建log对象
log = logging.getLogger('demo')
log.setLevel(logging.INFO)

# 2 创建Handle对象
screen_log = logging.StreamHandler()
screen_log.setLevel(logging.INFO)
screen_log.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 3 创建文件Handle对象
file_log = logging.FileHandler('demo2_anbo.log',encoding='utf-8')
file_log.setLevel(logging.DEBUG)
file_log.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 4 添加Handle
log.addHandler(screen_log)
log.addHandler(file_log)



log.debug('111')
log.info('222')
log.warning('333')
log.error('444')
log.critical('555')

