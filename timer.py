# -*- coding:utf-8 -*-
import time
from datetime import datetime

from log import logger


class Timer(object):

    def __init__(self, buy_time, sleep_interval=0.5):

        # '2018-09-28 22:45:50.000'
        self.buy_time = datetime.strptime(buy_time, "%Y-%m-%d %H:%M:%S.%f")
        self.sleep_interval = sleep_interval

    def start(self):
        logger.info('正在等待到达设定时间:%s' % self.buy_time)
        now_time = datetime.now
        while True:
            if now_time() >= self.buy_time:
                logger.info('时间到达，开始执行……')
                break
            else:
                time.sleep(self.sleep_interval)
