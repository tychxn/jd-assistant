#!/usr/bin/env python
# -*- coding:utf-8 -*-
from jd_assistant import Assistant

if __name__ == '__main__':
    """
    重要提示：此处为示例代码之一，请移步下面的链接查看使用教程👇
    https://github.com/tychxn/jd-assistant/wiki/1.-%E4%BA%AC%E4%B8%9C%E6%8A%A2%E8%B4%AD%E5%8A%A9%E6%89%8B%E7%94%A8%E6%B3%95
    """

    asst = Assistant()  # 初始化
    asst.login_by_QRcode()  # 扫码登陆
    asst.exec_seckill_by_time(sku_ids='100002852990', buy_time='2019-02-19 09:59:59.500', retry=10, interval=4)
    # 5个参数
    # sku_ids: 商品id，多个商品id用逗号进行分割，如"123,456,789"
    # buy_time: 下单时间，例如：'2019-02-19 09:59:59.500'
    # retry: 抢购重复执行次数，可选参数，默认4次
    # interval: 抢购执行间隔，可选参数，默认4秒
    # num: 购买数量，可选参数，默认1个
