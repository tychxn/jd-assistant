# JD-Assistant

[![version](https://img.shields.io/badge/python-3.4+-blue.svg)](https://www.python.org/download/releases/3.4.0/) 
[![status](https://img.shields.io/badge/status-stable-green.svg)](https://github.com/tychxn/jd-assistant)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![star, issue](https://img.shields.io/badge/star%2C%20issue-welcome-brightgreen.svg)](https://github.com/tychxn/jd-assistant)

京东抢购助手

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

[👉请参看Wiki](https://github.com/tychxn/jd-assistant/wiki/1.-%E4%BA%AC%E4%B8%9C%E6%8A%A2%E8%B4%AD%E5%8A%A9%E6%89%8B%E7%94%A8%E6%B3%95)


## 公告

- 【2019.09.27】经测试，扫码登录、加购物车、普通商品下单等功能正常，抢购商品下单存在问题（最近也没太多的商品是需要抢购下单的，数据包获取不够）
- 【2019.03.06】最近京东更新了抢购接口，出现网页端可以抢购成功，但是脚本抢购成功率非常低的情况。本人暂时查找不到原因，寻求各位的帮助。联系邮箱`tychxn@gmail.com`，非常感谢～

## 更新记录

- 【2019.02.16】更新了普通商品的抢购代码，在Wiki中写了一份使用教程。
- 【2018.11.29】京东更新了抢购商品的下单接口，代码已更新，支持定时抢购。
- 【2018.09.26】京东已下线`字符验证码`接口，`账号密码登录`功能失效，请使用扫码登录`asst.login_by_QRcode()`。
- 【2018.07.28】京东已采用`滑动验证码`替换登录时出现的`字符验证码`，但还没有下线`字符验证码`接口，`账号密码登录`功能依旧可用。等待后续更新滑动验证方式，推荐使用`扫码登录`。

## 备注

- 京东商城的登陆/下单机制经常改动，当前测试时间`2019.09.27`。如果失效，欢迎提issue，我会来更新。
- 图片查看器背景颜色为黑色时，二维码会出现无法扫描的情况 (多发于`win10`系统)，请更换软件打开图片。
- 代码在`macOS`中编写，如果在其他平台上运行出行问题，欢迎提issue。

## 待办列表

- [ ] 添加日志记录功能
