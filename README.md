# JD-Assistant

[![version](https://img.shields.io/badge/python-3.4+-blue.svg)](https://www.python.org/download/releases/3.4.0/) 
[![status](https://img.shields.io/badge/status-stable-green.svg)](https://github.com/tychxn/jd-assistant)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![star, issue](https://img.shields.io/badge/star%2C%20issue-welcome-brightgreen.svg)](https://github.com/tychxn/jd-assistant)

京东抢购助手

## 功能

- 模拟登陆京东商城（[www.jd.com](http://www.jd.com/)）
  - 账号密码登录 (如需验证码会提示输入)
  - 手机扫码登录
  - 保存/加载登录cookies (可验证cookies是否过期)
- 商品查询操作
  - 提供完整的[`地址⇔ID`](./area_id/)对应关系
  - 根据商品ID和地址ID查询库存
  - 根据商品ID查询价格
- 购物车操作
  - 添加/清空购物车 (无货商品也可以加入购物车，预约商品无法加入)
  - 获取购物车商品详情
- 订单提交操作
  - 获取订单结算页面信息 (商品详情, 应付总额, 收货地址, 收货人等)
  - 提交订单
- 订单查询操作
  - 获取个人中心订单信息 (可选择只显示未付款订单)

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

## Todo

- [x] 添加扫码登陆功能
- [x] 添加商品库存查询功能
- [x] 添加根据地址获取ID功能：暂时根据地址ID表对应查询
- [x] 添加商品价格查询功能 (后续分别添加获取网页端，APP端，手机QQ端，微信端价格)
- [x] 添加商品下单功能：添加购物车->结算页面->下单（仍需优化）
- [x] 检查本地保存的cookies是否过期
- [x] 获取登录用户信息：用户昵称等
- [x] 添加订单查询功能
- [x] 将`PyCrypto`库替换为[`PyCryptodome`](https://github.com/Legrandin/pycryptodome)
- [ ] 添加有货下单功能
- [ ] 添加定时下单功能
- [ ] 添加日志记录功能
- [ ] 编写使用文档
- [ ] 添加用户界面

## Remark

- 京东商城的登录机制经常改动，当前测试时间`2018.7.23`。如果失效，请在issue中提出，我会来更新。
- 使用帐号密码登陆时，第一次登陆可能会出现无需验证码但是登陆失败的情况，再次登陆就会提示需要验证码并正常登录。
- 图片查看器背景颜色为黑色时，二维码会出现无法扫描的情况 (多发于`win10`系统)，请更换软件打开图片。
