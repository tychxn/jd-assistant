# jd-login

## 功能

- 模拟登陆京东商城（jd.com）
  - 账号密码登录 (如需验证码会提示输入)
  - 手机扫码登录
- 保存/加载登录cookies
- 提供完整的京东地址对应ID以便查询
- 根据商品ID和地址ID查询库存
- 根据商品ID查询价格
- 添加/清空购物车 (无货商品也可以加入购物车，预约商品无法加入)

## 运行环境

- Python 3.5

## 第三方库

- [Requests](http://docs.python-requests.org/en/master/)
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [PyCrypto](https://www.dlitz.net/software/pycrypto/) ([Python3.5快速安装PyCrypto](https://github.com/sfbahr/PyCrypto-Wheels))

## Todo

- ~~添加扫码登陆功能~~
- ~~添加商品库存查询功能~~
- ~~添加根据地址获取ID功能~~（暂时根据地址ID表对应查询）
- ~~添加商品价格查询功能~~ (计划添加分别获取网页端，APP端，手机QQ端，微信端价格)
- 添加商品下单功能 (~~添加购物车~~->结算页面->下单)
- 检查本地保存的cookies是否过期
- 添加订单查询功能
- 添加用户界面

## Remark

- 京东商城的登录机制经常改动，当前测试时间`2018.7.2`。如果失效，请在issue中提出，我会来更新。
- 使用帐号密码登陆时，第一次登陆可能会出现无需验证码但是登陆失败的情况，再次登陆就会提示需要验证码并正常登录。
