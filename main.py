#!/usr/bin/env python
# -*- coding:utf-8 -*-
from jd_assistant import Assistant

if __name__ == '__main__':
    asst = Assistant()
    asst.login_by_username()
    # asst.login_by_QRcode()
    print(asst.get_item_stock_state(sku_id='5089267', area='12_904_3375'))
    print(asst.get_item_price(sku_id='5089267'))
    asst.clear_cart()
    asst.add_item_to_cart(sku_id='5089267')
    asst.get_cart_detail()
    asst.get_checkout_page_detail()
    print(asst.get_user_info())
    # asst.submit_order()
    asst.get_order_info(unpaid=False)
