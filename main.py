#!/usr/bin/env python
# -*- coding:utf-8 -*-
from jd_assistant import Assistant

if __name__ == '__main__':
    asst = Assistant()
    asst.login_by_QRcode()  # 扫码登陆
    asst.clear_cart()  # 清空购物车
    asst.add_item_to_cart(sku_id='1626336666')  # 添加到购物车

    # 3种订单提交方式：
    # 1.直接提交订单
    # asst.submit_order()
    # 2.有货时提交订单
    asst.submit_order_by_stock(sku_id='1626336666', area='1_2802_2821')  # 监控的商品id和地址id
    # 3.定时提交订单
    # asst.submit_order_by_time(buy_time='2018-10-19 00:00:00.500', retry=3, interval=5)

    asst.get_order_info(unpaid=False)  # 查询未付款订单

    """
    输出实例：
    [2018-10-19 02:38:58] 登录成功
    [2018-10-19 02:38:58] 购物车清空成功
    [2018-10-19 02:38:58] 1626336666已成功加入购物车
    [2018-10-19 02:38:59] 1626336666有货了，正在提交订单……
    [2018-10-19 02:38:59] 订单提交成功! 订单号：811545xxxxx
    ************************订单列表页查询************************
    订单号:811545xxxxx----下单时间:2018-10-19 02:38:59----商品列表:1626336666 x 1----订单状态:等待付款----总金额:89.90元----付款方式:在线支付
    """