# JD-Assistant

[![version](https://img.shields.io/badge/python-3.4+-blue.svg)](https://www.python.org/download/releases/3.4.0/) 
[![status](https://img.shields.io/badge/status-stable-green.svg)](https://github.com/tychxn/jd-assistant)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![star, issue](https://img.shields.io/badge/star%2C%20issue-welcome-brightgreen.svg)](https://github.com/tychxn/jd-assistant)

京东抢购助手（短期内不再更新）

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

👉 [使用教程请参看Wiki](https://github.com/tychxn/jd-assistant/wiki/1.-%E4%BA%AC%E4%B8%9C%E6%8A%A2%E8%B4%AD%E5%8A%A9%E6%89%8B%E7%94%A8%E6%B3%95)


## 更新记录

- 【2020.03.10】修复了一些小问题。
- 【2020.02.08】修复了查询库存接口响应数据结构变化导致的问题。
- 【2020.02.06】添加下单成功消息推送功能；新增配置参数以减少各种异常情况。
- 【2020.02.03】查询商品库存方法添加超时，避免少数情况下的卡死问题；对部分代码进行了优化。
- 【2020.02.02】重写了监控库存提交订单功能：监控多商品时可以下单任一有库存商品，具体使用方式请参考wiki。
- 【2020.01.29】修复了自定义商品数量时的bug。
- 【2020.01.28】完善了监控库存提交订单功能的代码，具体使用方式请参考wiki。
- 【2020.01.24】修复了查询单个商品库存接口需要添加额外参数的问题。
- 【2020.01.15】提升了部分代码质量。
- 【2019.12.14】解决查询单个商品库存接口变动的问题。
- 【2019.11.10】临时增加预约商品抢购功能。
- 【2019.02.16】更新了普通商品的抢购代码，在Wiki中写了一份使用教程。
- 【2018.11.29】京东更新了抢购商品的下单接口，代码已更新，支持定时抢购。
- 【2018.09.26】京东已下线`字符验证码`接口，`账号密码登录`功能失效，请使用扫码登录`asst.login_by_QRcode()`。
- 【2018.07.28】京东已采用`滑动验证码`替换登录时出现的`字符验证码`，但还没有下线`字符验证码`接口，`账号密码登录`功能依旧可用。等待后续更新滑动验证方式，推荐使用`扫码登录`。

## 备注

- 🌟强烈建议大家在部署代码前使用有货的商品测试下单流程，并且：在京东购物车结算页面设置发票为`电子普通发票-个人`，设置支付方式为`在线支付`，否则可能出现各种未知的下单失败问题。🌟
- 京东商城的登陆/下单机制经常改动，当前测试时间`2020.02.08`。如果失效，欢迎提issue，我会来更新。
- 代码在`macOS`中编写，如果在其他平台上运行出行问题，欢迎提issue。

## 待完成的功能

- [ ] Keep session alive
- [ ] 抢优惠券

## 不考虑的功能

- ✖️ 支付功能
- ✖️ 多账号抢购

## Sponsor

[![JetBrains](./docs/jetbrains.svg)](https://www.jetbrains.com/?from=jd-assistant)
