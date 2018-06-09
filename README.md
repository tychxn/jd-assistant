# jd-login

## 功能

- 模拟登陆京东商城（jd.com）
  - 账号密码登录 (可能有验证码)
  - 手机扫码登录
- 保存/加载登录cookies

## 运行环境

- Python 3.5

## 第三方库

- [Requests](http://docs.python-requests.org/en/master/)
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [PyCrypto](https://www.dlitz.net/software/pycrypto/) ([Python3.5快速安装PyCrypto](https://github.com/sfbahr/PyCrypto-Wheels))

## Todo

- ~~添加扫码登陆功能~~
- 添加商品下单功能
- 添加用户界面

## Remark

- 京东商城的登录机制经常改动，当前测试时间2018.6.9。如果失效，请在issue中提出，我会来更新。
