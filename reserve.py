#!/usr/bin/env python
# -*- coding:utf-8 -*-
from jd_assistant import Assistant

if __name__ == '__main__':
    asst = Assistant()  # 初始化
    asst.login_by_QRcode()  # 扫码登陆
    asst.make_reserve(sku_id='3335316', buy_time='2020-02-16 21:01:00.000')
    #asst.make_reserve(sku_id='100011385146', buy_time='2020-02-16 15:00:00.000')
    #asst.make_reserve(sku_id='100011328834', buy_time='2020-02-16 15:01:00.000')
    # 执行预约抢购
    # 2个参数
    # sku_id: 商品id
    # buy_time: 预约时间，例如：'2019-11-10 22:41:30.000'
