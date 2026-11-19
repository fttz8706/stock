#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import time
import datetime
import concurrent.futures
import logging
import os.path
import sys

# 在项目运行时，临时将项目路径添加到环境变量
cpath_current = os.path.dirname(os.path.dirname(__file__))
cpath = os.path.abspath(os.path.join(cpath_current, os.pardir))
sys.path.append(cpath)
log_path = os.path.join(cpath_current, 'log')
if not os.path.exists(log_path):
    os.makedirs(log_path, exist_ok=True)
logging.basicConfig(format='%(asctime)s %(message)s', filename=os.path.join(log_path, 'stock_execute_job.log'))
logging.getLogger().setLevel(logging.INFO)
import init_job as bj
import basic_data_daily_job as hdj
import basic_data_other_daily_job as hdtj
import basic_data_after_close_daily_job as acdj
import indicators_data_daily_job as gdj
import strategy_data_daily_job as sdj
import backtest_data_daily_job as bdj
import klinepattern_data_daily_job as kdj
import selection_data_daily_job as sddj

__author__ = 'myh '
__date__ = '2023/3/10 '


def _run_jobs():
    start = time.time()
    _start = datetime.datetime.now()
    logging.info("######## 任务执行时间: %s #######" % _start.strftime("%Y-%m-%d %H:%M:%S.%f"))
    # 第1步创建数据库
    bj.main()
    # 第2.1步创建股票基础数据表
    hdj.main()
    # 第2.2步创建综合股票数据表
    sddj.main()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(job.main) for job in (hdtj, gdj, kdj, sdj)]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    bdj.main()

    # # # # 第7步创建股票闭盘后才有的数据
    acdj.main()




class JobErrorCounter(logging.Handler):
    def __init__(self):
        super().__init__(logging.ERROR)
        self.count = 0

    def emit(self, record):
        self.count += 1


def main():
    counter = JobErrorCounter()
    logger = logging.getLogger()
    logger.addHandler(counter)
    try:
        _run_jobs()
    finally:
        logger.removeHandler(counter)
    if counter.count:
        raise RuntimeError(f"任务部分失败：记录了 {counter.count} 个错误，请检查采集日志")
    logging.info("######## 完成任务（未记录错误） #######")


# main函数入口
if __name__ == '__main__':
    main()
