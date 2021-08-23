# JD-Assistant

[![version](https://img.shields.io/badge/python-3.4+-blue.svg)](https://www.python.org/download/releases/3.4.0/) 
[![status](https://img.shields.io/badge/status-stable-green.svg)](https://github.com/huaisha1224/jd-assistant)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![star, issue](https://img.shields.io/badge/star%2C%20issue-welcome-brightgreen.svg)](https://github.com/huaisha1224/jd-assistant)

京东抢购助手源代码Fork自https://github.com/tychxn/jd-assistant
-由于原作者已不再更新、刚好我又有需要、所以在此基础上进行了修改；

## 主要功能

- 登陆京东商城（[www.jd.com](http://www.jd.com/)）
  - 手机扫码登录
  - 保存/加载登录cookies (可验证cookies是否过期)
- 商品查询操作
  - 提供完整的[`地址⇔ID`](./area_id/)对应关系
  - 根据商品ID和地址ID查询库存
  - 根据商品ID查询价格
- 购物车操作
  - 清空/添加购物车 (无货商品也可以加入购物车，预约商品无法加入)
  - 获取购物车商品详情
- 订单操作
  - 获取订单结算页面信息 (商品详情, 应付总额, 收货地址, 收货人等)
  - 提交订单（使用默认地址）
    - 直接提交
    - 有货提交
    - 定时提交
  - 查询订单 (可选择只显示未付款订单)
  - 查询本地生活服务订单中的验证码及其状态(验证码是否已消费)
- 其他
  - 商品预约
  - 用户信息查询

## 运行环境

- [Python 3](https://www.python.org/)

## 第三方库

- [Requests](http://docs.python-requests.org/en/master/)
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [PyCryptodome](https://github.com/Legrandin/pycryptodome)

安装：
```sh
pip install -r requirements.txt
```

## 使用教程

程序主入口在 `main.py`

👉 [使用教程请参看Wiki](https://github.com/huaisha1224/jd-assistant/wiki/%E4%BA%AC%E4%B8%9C%E6%8A%A2%E8%B4%AD%E5%8A%A9%E6%89%8B)


## 更新记录
- 【2021.08.23】增加shimo.py模块、支持提交数据到石墨文档
- 【2021.08.12】优化代码、输出增加验证码消费时间
- 【2021.08.05】优化代码、处理某些特殊订单获取不到验证码的情况
- 【2021.08.03】优化代码、处理cookies失败情况下的异常情况
- 【2021.07.22】在原作者代码基础上、增加了查询订单验证码功能

## 备注

- 🌟强烈建议大家在部署代码前使用有货的商品测试下单流程，并且：在京东购物车结算页面设置发票为`电子普通发票-个人`，设置支付方式为`在线支付`，否则可能出现各种未知的下单失败问题。🌟
- 京东商城的登陆/下单机制经常改动，原jd-assistant最后一次更新时间时间`2020.03.08`。如果功能失效，欢迎提issue，有时间我会来更新。
- 代码在`Win10`中编写，如果在其他平台上运行出行问题，欢迎提issue。

## 待完成的功能
- [✔] 订单验证码查询
- [ ] 抢优惠券

## 不考虑的功能

- ✖️ 支付功能
- ✖️ 多账号抢购
