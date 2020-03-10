#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import pickle
import re
import random
import time

import requests
from bs4 import BeautifulSoup

from config import global_config
from exception import AsstException
from log import logger
from messenger import Messenger
from timer import Timer
from util import (
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    check_login,
    deprecated,
    encrypt_pwd,
    encrypt_payment_pwd,
    get_tag_value,
    get_random_useragent,
    open_image,
    parse_area_id,
    parse_json,
    parse_sku_id,
    parse_items_dict,
    response_status,
    save_image,
    split_area_id
)


class Assistant(object):

    def __init__(self):
        use_random_ua = global_config.getboolean('config', 'random_useragent')
        self.user_agent = DEFAULT_USER_AGENT if not use_random_ua else get_random_useragent()
        self.headers = {'User-Agent': self.user_agent}
        self.eid = global_config.get('config', 'eid')
        self.fp = global_config.get('config', 'fp')
        self.track_id = global_config.get('config', 'track_id')
        self.risk_control = global_config.get('config', 'risk_control')
        if not self.eid or not self.fp or not self.track_id or not self.risk_control:
            raise AsstException('请在 config.ini 中配置 eid, fp, track_id, risk_control 参数，具体请参考 wiki-常见问题')

        self.timeout = float(global_config.get('config', 'timeout') or DEFAULT_TIMEOUT)
        self.send_message = global_config.getboolean('messenger', 'enable')
        self.messenger = Messenger(global_config.get('messenger', 'sckey')) if self.send_message else None

        self.item_cat = dict()
        self.item_vender_ids = dict()  # 记录商家id

        self.seckill_init_info = dict()
        self.seckill_order_data = dict()
        self.seckill_url = dict()

        self.username = ''
        self.nick_name = ''
        self.is_login = False
        self.sess = requests.session()
        try:
            self._load_cookies()
        except Exception:
            pass

    def _load_cookies(self):
        cookies_file = ''
        for name in os.listdir('./cookies'):
            if name.endswith('.cookies'):
                cookies_file = './cookies/{0}'.format(name)
                break
        with open(cookies_file, 'rb') as f:
            local_cookies = pickle.load(f)
        self.sess.cookies.update(local_cookies)
        self.is_login = self._validate_cookies()

    def _save_cookies(self):
        cookies_file = './cookies/{0}.cookies'.format(self.nick_name)
        directory = os.path.dirname(cookies_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(cookies_file, 'wb') as f:
            pickle.dump(self.sess.cookies, f)

    def _validate_cookies(self):
        """验证cookies是否有效（是否登陆）
        通过访问用户订单列表页进行判断：若未登录，将会重定向到登陆页面。
        :return: cookies是否有效 True/False
        """
        url = 'https://order.jd.com/center/list.action'
        payload = {
            'rid': str(int(time.time() * 1000)),
        }
        try:
            resp = self.sess.get(url=url, params=payload, allow_redirects=False)
            if resp.status_code == requests.codes.OK:
                return True
        except Exception as e:
            logger.error(e)

        self.sess = requests.session()
        return False

    @deprecated
    def _need_auth_code(self, username):
        url = 'https://passport.jd.com/uc/showAuthCode'
        data = {
            'loginName': username,
        }
        payload = {
            'version': 2015,
            'r': random.random(),
        }
        resp = self.sess.post(url, params=payload, data=data, headers=self.headers)
        if not response_status(resp):
            logger.error('获取是否需要验证码失败')
            return False

        resp_json = json.loads(resp.text[1:-1])  # ({"verifycode":true})
        return resp_json['verifycode']

    @deprecated
    def _get_auth_code(self, uuid):
        image_file = os.path.join(os.getcwd(), 'jd_authcode.jpg')

        url = 'https://authcode.jd.com/verify/image'
        payload = {
            'a': 1,
            'acid': uuid,
            'uid': uuid,
            'yys': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://passport.jd.com/uc/login',
        }
        resp = self.sess.get(url, params=payload, headers=headers)

        if not response_status(resp):
            logger.error('获取验证码失败')
            return ''

        save_image(resp, image_file)
        open_image(image_file)
        return input('验证码:')

    def _get_login_page(self):
        url = "https://passport.jd.com/new/login.aspx"
        page = self.sess.get(url, headers=self.headers)
        return page

    @deprecated
    def _get_login_data(self):
        page = self._get_login_page()
        soup = BeautifulSoup(page.text, "html.parser")
        input_list = soup.select('.form input')

        # eid & fp are generated by local javascript code according to browser environment
        return {
            'sa_token': input_list[0]['value'],
            'uuid': input_list[1]['value'],
            '_t': input_list[4]['value'],
            'loginType': input_list[5]['value'],
            'pubKey': input_list[7]['value'],
            'eid': self.eid,
            'fp': self.fp,
        }

    @deprecated
    def login_by_username(self):
        if self.is_login:
            logger.info('登录成功')
            return True

        username = input('账号:')
        password = input('密码:')
        if (not username) or (not password):
            logger.error('用户名或密码不能为空')
            return False
        self.username = username

        data = self._get_login_data()
        uuid = data['uuid']

        auth_code = ''
        if self._need_auth_code(username):
            logger.info('本次登录需要验证码')
            auth_code = self._get_auth_code(uuid)
        else:
            logger.info('本次登录不需要验证码')

        login_url = "https://passport.jd.com/uc/loginService"
        payload = {
            'uuid': uuid,
            'version': 2015,
            'r': random.random(),
        }
        data['authcode'] = auth_code
        data['loginname'] = username
        data['nloginpwd'] = encrypt_pwd(password)
        headers = {
            'User-Agent': self.user_agent,
            'Origin': 'https://passport.jd.com',
        }
        resp = self.sess.post(url=login_url, data=data, headers=headers, params=payload)

        if not response_status(resp):
            logger.error('登录失败')
            return False

        if not self._get_login_result(resp):
            return False

        # login success
        logger.info('登录成功')
        self.nick_name = self.get_user_info()
        self._save_cookies()
        self.is_login = True
        return True

    @deprecated
    def _get_login_result(self, resp):
        resp_json = parse_json(resp.text)
        error_msg = ''
        if 'success' in resp_json:
            # {"success":"http://www.jd.com"}
            return True
        elif 'emptyAuthcode' in resp_json:
            # {'_t': '_t', 'emptyAuthcode': '请输入验证码'}
            # {'_t': '_t', 'emptyAuthcode': '验证码不正确或验证码已过期'}
            error_msg = resp_json['emptyAuthcode']
        elif 'username' in resp_json:
            # {'_t': '_t', 'username': '账户名不存在，请重新输入'}
            # {'username': '服务器繁忙，请稍后再试', 'venture': 'xxxx', 'p': 'xxxx', 'ventureRet': 'http://www.jd.com/', '_t': '_t'}
            if resp_json['username'] == '服务器繁忙，请稍后再试':
                error_msg = resp_json['username'] + '(预计账户存在风险，需短信激活)'
            else:
                error_msg = resp_json['username']
        elif 'pwd' in resp_json:
            # {'pwd': '账户名与密码不匹配，请重新输入', '_t': '_t'}
            error_msg = resp_json['pwd']
        else:
            error_msg = resp_json
        logger.error(error_msg)
        return False

    def _get_QRcode(self):
        url = 'https://qr.m.jd.com/show'
        payload = {
            'appid': 133,
            'size': 147,
            't': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://passport.jd.com/new/login.aspx',
        }
        resp = self.sess.get(url=url, headers=headers, params=payload)

        if not response_status(resp):
            logger.info('获取二维码失败')
            return False

        QRCode_file = 'QRcode.png'
        save_image(resp, QRCode_file)
        logger.info('二维码获取成功，请打开京东APP扫描')
        open_image(QRCode_file)
        return True

    def _get_QRcode_ticket(self):
        url = 'https://qr.m.jd.com/check'
        payload = {
            'appid': '133',
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            'token': self.sess.cookies.get('wlfstk_smdl'),
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://passport.jd.com/new/login.aspx',
        }
        resp = self.sess.get(url=url, headers=headers, params=payload)

        if not response_status(resp):
            logger.error('获取二维码扫描结果异常')
            return False

        resp_json = parse_json(resp.text)
        if resp_json['code'] != 200:
            logger.info('Code: %s, Message: %s', resp_json['code'], resp_json['msg'])
            return None
        else:
            logger.info('已完成手机客户端确认')
            return resp_json['ticket']

    def _validate_QRcode_ticket(self, ticket):
        url = 'https://passport.jd.com/uc/qrCodeTicketValidation'
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://passport.jd.com/uc/login?ltype=logout',
        }
        resp = self.sess.get(url=url, headers=headers, params={'t': ticket})

        if not response_status(resp):
            return False

        resp_json = json.loads(resp.text)
        if resp_json['returnCode'] == 0:
            return True
        else:
            logger.info(resp_json)
            return False

    def login_by_QRcode(self):
        """二维码登陆
        :return:
        """
        if self.is_login:
            logger.info('登录成功')
            return

        self._get_login_page()

        # download QR code
        if not self._get_QRcode():
            raise AsstException('二维码下载失败')

        # get QR code ticket
        ticket = None
        retry_times = 85
        for _ in range(retry_times):
            ticket = self._get_QRcode_ticket()
            if ticket:
                break
            time.sleep(2)
        else:
            raise AsstException('二维码过期，请重新获取扫描')

        # validate QR code ticket
        if not self._validate_QRcode_ticket(ticket):
            raise AsstException('二维码信息校验失败')

        logger.info('二维码登录成功')
        self.is_login = True
        self.nick_name = self.get_user_info()
        self._save_cookies()

    def _get_reserve_url(self, sku_id):
        url = 'https://yushou.jd.com/youshouinfo.action'
        payload = {
            'callback': 'fetchJSON',
            'sku': sku_id,
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://item.jd.com/{}.html'.format(sku_id),
        }
        resp = self.sess.get(url=url, params=payload, headers=headers)
        resp_json = parse_json(resp.text)
        # {"type":"1","hasAddress":false,"riskCheck":"0","flag":false,"num":941723,"stime":"2018-10-12 12:40:00","plusEtime":"","qiangEtime":"","showPromoPrice":"0","qiangStime":"","state":2,"sku":100000287121,"info":"\u9884\u7ea6\u8fdb\u884c\u4e2d","isJ":0,"address":"","d":48824,"hidePrice":"0","yueEtime":"2018-10-19 15:01:00","plusStime":"","isBefore":0,"url":"//yushou.jd.com/toYuyue.action?sku=100000287121&key=237af0174f1cffffd227a2f98481a338","etime":"2018-10-19 15:01:00","plusD":48824,"category":"4","plusType":0,"yueStime":"2018-10-12 12:40:00"};
        reserve_url = resp_json.get('url')
        return 'https:' + reserve_url if reserve_url else None

    @check_login
    def make_reserve(self, sku_id):
        """商品预约
        :param sku_id: 商品id
        :return:
        """
        reserve_url = self._get_reserve_url(sku_id)
        if not reserve_url:
            logger.error('%s 非预约商品', sku_id)
            return
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://item.jd.com/{}.html'.format(sku_id),
        }
        resp = self.sess.get(url=reserve_url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        reserve_result = soup.find('p', {'class': 'bd-right-result'}).text.strip(' \t\r\n')
        # 预约成功，已获得抢购资格 / 您已成功预约过了，无需重复预约
        logger.info(reserve_result)

    @check_login
    def get_user_info(self):
        """获取用户信息
        :return: 用户名
        """
        url = 'https://passport.jd.com/user/petName/getUserInfoForMiniJd.action'
        payload = {
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://order.jd.com/center/list.action',
        }
        try:
            resp = self.sess.get(url=url, params=payload, headers=headers)
            resp_json = parse_json(resp.text)
            # many user info are included in response, now return nick name in it
            # jQuery2381773({"imgUrl":"//storage.360buyimg.com/i.imageUpload/xxx.jpg","lastLoginTime":"","nickName":"xxx","plusStatus":"0","realName":"xxx","userLevel":x,"userScoreVO":{"accountScore":xx,"activityScore":xx,"consumptionScore":xxxxx,"default":false,"financeScore":xxx,"pin":"xxx","riskScore":x,"totalScore":xxxxx}})
            return resp_json.get('nickName') or 'jd'
        except Exception:
            return 'jd'

    def _get_item_detail_page(self, sku_id):
        """访问商品详情页
        :param sku_id: 商品id
        :return: 响应
        """
        url = 'https://item.jd.com/{}.html'.format(sku_id)
        page = requests.get(url=url, headers=self.headers)
        return page

    def get_single_item_stock(self, sku_id, num, area):
        """获取单个商品库存状态
        :param sku_id: 商品id
        :param num: 商品数量
        :param area: 地区id
        :return: 商品是否有货 True/False
        """
        area_id = parse_area_id(area)

        cat = self.item_cat.get(sku_id)
        vender_id = self.item_vender_ids.get(sku_id)
        if not cat:
            page = self._get_item_detail_page(sku_id)
            match = re.search(r'cat: \[(.*?)\]', page.text)
            cat = match.group(1)
            self.item_cat[sku_id] = cat

            match = re.search(r'venderId:(\d*?),', page.text)
            vender_id = match.group(1)
            self.item_vender_ids[sku_id] = vender_id

        url = 'https://c0.3.cn/stock'
        payload = {
            'skuId': sku_id,
            'buyNum': num,
            'area': area_id,
            'ch': 1,
            '_': str(int(time.time() * 1000)),
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            'extraParam': '{"originid":"1"}',  # get error stock state without this param
            'cat': cat,  # get 403 Forbidden without this param (obtained from the detail page)
            'venderId': vender_id  # return seller information with this param (can't be ignored)
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://item.jd.com/{}.html'.format(sku_id),
        }

        resp_text = ''
        try:
            resp_text = requests.get(url=url, params=payload, headers=headers, timeout=self.timeout).text
            resp_json = parse_json(resp_text)
            stock_info = resp_json.get('stock')
            sku_state = stock_info.get('skuState')  # 商品是否上架
            stock_state = stock_info.get('StockState')  # 商品库存状态：33 -- 现货  0,34 -- 无货  36 -- 采购中  40 -- 可配货
            return sku_state == 1 and stock_state in (33, 40)
        except requests.exceptions.Timeout:
            logger.error('查询 %s 库存信息超时(%ss)', sku_id, self.timeout)
            return False
        except requests.exceptions.RequestException as request_exception:
            logger.error('查询 %s 库存信息发生网络请求异常：%s', sku_id, request_exception)
            return False
        except Exception as e:
            logger.error('查询 %s 库存信息发生异常, resp: %s, exception: %s', sku_id, resp_text, e)
            return False

    @check_login
    def get_multi_item_stock(self, sku_ids, area):
        """获取多个商品库存状态（旧）

        该方法需要登陆才能调用，用于同时查询多个商品的库存。
        京东查询接口返回每种商品的状态：有货/无货。当所有商品都有货，返回True；否则，返回False。

        :param sku_ids: 多个商品的id。可以传入中间用英文逗号的分割字符串，如"123,456"
        :param area: 地区id
        :return: 多个商品是否同时有货 True/False
        """
        items_dict = parse_sku_id(sku_ids=sku_ids)
        area_id_list = split_area_id(area)

        url = 'https://trade.jd.com/api/v1/batch/stock'
        headers = {
            'User-Agent': self.user_agent,
            'Origin': 'https://trade.jd.com',
            'Content-Type': 'application/json; charset=UTF-8',
            'Referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action?rid=' + str(int(time.time() * 1000)),
        }
        data = {
            "areaRequest": {
                "provinceId": area_id_list[0],
                "cityId": area_id_list[1],
                "countyId": area_id_list[2],
                "townId": area_id_list[3]
            },
            "skuNumList": []
        }
        for sku_id, count in items_dict.items():
            data['skuNumList'].append({
                "skuId": sku_id,
                "num": count
            })
        # convert to string
        data = json.dumps(data)

        try:
            resp = self.sess.post(url=url, headers=headers, data=data, timeout=self.timeout)
        except requests.exceptions.Timeout:
            logger.error('查询 %s 库存信息超时(%ss)', list(items_dict.keys()), self.timeout)
            return False
        except requests.exceptions.RequestException as e:
            raise AsstException('查询 %s 库存信息异常：%s' % (list(items_dict.keys()), e))

        resp_json = parse_json(resp.text)
        result = resp_json.get('result')

        stock = True
        for sku_id in result:
            status = result.get(sku_id).get('status')
            if '无货' in status:
                stock = False
                break

        return stock

    def get_multi_item_stock_new(self, sku_ids, area):
        """获取多个商品库存状态（新）

        当所有商品都有货，返回True；否则，返回False。

        :param sku_ids: 多个商品的id。可以传入中间用英文逗号的分割字符串，如"123,456"
        :param area: 地区id
        :return: 多个商品是否同时有货 True/False
        """
        items_dict = parse_sku_id(sku_ids=sku_ids)
        area_id = parse_area_id(area=area)

        url = 'https://c0.3.cn/stocks'
        payload = {
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            'type': 'getstocks',
            'skuIds': ','.join(items_dict.keys()),
            'area': area_id,
            '_': str(int(time.time() * 1000))
        }
        headers = {
            'User-Agent': self.user_agent
        }

        resp_text = ''
        try:
            resp_text = requests.get(url=url, params=payload, headers=headers, timeout=self.timeout).text
            stock = True
            for sku_id, info in parse_json(resp_text).items():
                sku_state = info.get('skuState')  # 商品是否上架
                stock_state = info.get('StockState')  # 商品库存状态
                if sku_state == 1 and stock_state in (33, 40):
                    continue
                else:
                    stock = False
                    break
            return stock
        except requests.exceptions.Timeout:
            logger.error('查询 %s 库存信息超时(%ss)', list(items_dict.keys()), self.timeout)
            return False
        except requests.exceptions.RequestException as request_exception:
            logger.error('查询 %s 库存信息发生网络请求异常：%s', list(items_dict.keys()), request_exception)
            return False
        except Exception as e:
            logger.error('查询 %s 库存信息发生异常, resp: %s, exception: %s', list(items_dict.keys()), resp_text, e)
            return False

    def _if_item_removed(self, sku_id):
        """判断商品是否下架
        :param sku_id: 商品id
        :return: 商品是否下架 True/False
        """
        detail_page = self._get_item_detail_page(sku_id=sku_id)
        return '该商品已下柜' in detail_page.text

    @check_login
    def if_item_can_be_ordered(self, sku_ids, area):
        """判断商品是否能下单
        :param sku_ids: 商品id，多个商品id中间使用英文逗号进行分割
        :param area: 地址id
        :return: 商品是否能下单 True/False
        """
        items_dict = parse_sku_id(sku_ids=sku_ids)
        area_id = parse_area_id(area)

        # 判断商品是否能下单
        if len(items_dict) > 1:
            return self.get_multi_item_stock_new(sku_ids=items_dict, area=area_id)

        sku_id, count = list(items_dict.items())[0]
        return self.get_single_item_stock(sku_id=sku_id, num=count, area=area_id)

    def get_item_price(self, sku_id):
        """获取商品价格
        :param sku_id: 商品id
        :return: 价格
        """
        url = 'http://p.3.cn/prices/mgets'
        payload = {
            'type': 1,
            'pduid': int(time.time() * 1000),
            'skuIds': 'J_' + sku_id,
        }
        resp = self.sess.get(url=url, params=payload)
        return parse_json(resp.text).get('p')

    @check_login
    def add_item_to_cart(self, sku_ids):
        """添加商品到购物车

        重要：
        1.商品添加到购物车后将会自动被勾选✓中。
        2.在提交订单时会对勾选的商品进行结算。
        3.部分商品（如预售、下架等）无法添加到购物车

        京东购物车可容纳的最大商品种数约为118-120种，超过数量会加入购物车失败。

        :param sku_ids: 商品id，格式："123" 或 "123,456" 或 "123:1,456:2"。若不配置数量，默认为1个。
        :return:
        """
        url = 'https://cart.jd.com/gate.action'
        headers = {
            'User-Agent': self.user_agent,
        }

        for sku_id, count in parse_sku_id(sku_ids=sku_ids).items():
            payload = {
                'pid': sku_id,
                'pcount': count,
                'ptype': 1,
            }
            resp = self.sess.get(url=url, params=payload, headers=headers)
            if 'https://cart.jd.com/cart.action' in resp.url:  # 套装商品加入购物车后直接跳转到购物车页面
                result = True
            else:  # 普通商品成功加入购物车后会跳转到提示 "商品已成功加入购物车！" 页面
                soup = BeautifulSoup(resp.text, "html.parser")
                result = bool(soup.select('h3.ftx-02'))  # [<h3 class="ftx-02">商品已成功加入购物车！</h3>]

            if result:
                logger.info('%s x %s 已成功加入购物车', sku_id, count)
            else:
                logger.error('%s 添加到购物车失败', sku_id)

    @check_login
    def clear_cart(self):
        """清空购物车

        包括两个请求：
        1.选中购物车中所有的商品
        2.批量删除

        :return: 清空购物车结果 True/False
        """
        # 1.select all items  2.batch remove items
        select_url = 'https://cart.jd.com/selectAllItem.action'
        remove_url = 'https://cart.jd.com/batchRemoveSkusFromCart.action'
        data = {
            't': 0,
            'outSkus': '',
            'random': random.random(),
        }
        try:
            select_resp = self.sess.post(url=select_url, data=data)
            remove_resp = self.sess.post(url=remove_url, data=data)
            if (not response_status(select_resp)) or (not response_status(remove_resp)):
                logger.error('购物车清空失败')
                return False
            logger.info('购物车清空成功')
            return True
        except Exception as e:
            logger.error(e)
            return False

    @check_login
    def get_cart_detail(self):
        """获取购物车商品详情
        :return: 购物车商品信息 dict
        """
        url = 'https://cart.jd.com/cart.action'
        resp = self.sess.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        cart_detail = dict()
        for item in soup.find_all(class_='item-item'):
            try:
                sku_id = item['skuid']  # 商品id
                # 例如：['increment', '8888', '100001071956', '1', '13', '0', '50067652554']
                # ['increment', '8888', '100002404322', '2', '1', '0']
                item_attr_list = item.find(class_='increment')['id'].split('_')
                p_type = item_attr_list[4]
                promo_id = target_id = item_attr_list[-1] if len(item_attr_list) == 7 else 0

                cart_detail[sku_id] = {
                    'name': get_tag_value(item.select('div.p-name a')),  # 商品名称
                    'verder_id': item['venderid'],  # 商家id
                    'count': int(item['num']),  # 数量
                    'unit_price': get_tag_value(item.select('div.p-price strong'))[1:],  # 单价
                    'total_price': get_tag_value(item.select('div.p-sum strong'))[1:],  # 总价
                    'is_selected': 'item-selected' in item['class'],  # 商品是否被勾选
                    'p_type': p_type,
                    'target_id': target_id,
                    'promo_id': promo_id
                }
            except Exception as e:
                logger.error("某商品在购物车中的信息无法解析，报错信息: %s，该商品自动忽略。 %s", e, item)

        logger.info('购物车信息：%s', cart_detail)
        return cart_detail

    def _cancel_select_all_cart_item(self):
        """取消勾选购物车中的所有商品
        :return: 取消勾选结果 True/False
        """
        url = "https://cart.jd.com/cancelAllItem.action"
        data = {
            't': 0,
            'outSkus': '',
            'random': random.random()
            # 'locationId' can be ignored
        }
        resp = self.sess.post(url, data=data)
        return response_status(resp)

    def _change_item_num_in_cart(self, sku_id, vender_id, num, p_type, target_id, promo_id):
        """修改购物车商品的数量
        修改购物车中商品数量后，该商品将会被自动勾选上。

        :param sku_id: 商品id
        :param vender_id: 商家id
        :param num: 目标数量
        :param p_type: 商品类型(可能)
        :param target_id: 参数用途未知，可能是用户判断优惠
        :param promo_id: 参数用途未知，可能是用户判断优惠
        :return: 商品数量修改结果 True/False
        """
        url = "https://cart.jd.com/changeNum.action"
        data = {
            't': 0,
            'venderId': vender_id,
            'pid': sku_id,
            'pcount': num,
            'ptype': p_type,
            'targetId': target_id,
            'promoID': promo_id,
            'outSkus': '',
            'random': random.random(),
            # 'locationId'
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://cart.jd.com/cart',
        }
        resp = self.sess.post(url, data=data, headers=headers)
        return json.loads(resp.text)['sortedWebCartResult']['achieveSevenState'] == 2

    def _add_or_change_cart_item(self, cart, sku_id, count):
        """添加商品到购物车，或修改购物车中商品数量

        如果购物车中存在该商品，会修改该商品的数量并勾选；否则，会添加该商品到购物车中并勾选。

        :param cart: 购物车信息 dict
        :param sku_id: 商品id
        :param count: 商品数量
        :return: 运行结果 True/False
        """
        if sku_id in cart:
            logger.info('%s 已在购物车中，调整数量为 %s', sku_id, count)
            cart_item = cart.get(sku_id)
            return self._change_item_num_in_cart(
                sku_id=sku_id,
                vender_id=cart_item.get('vender_id'),
                num=count,
                p_type=cart_item.get('p_type'),
                target_id=cart_item.get('target_id'),
                promo_id=cart_item.get('promo_id')
            )
        else:
            logger.info('%s 不在购物车中，开始加入购物车，数量 %s', sku_id, count)
            return self.add_item_to_cart(sku_ids={sku_id: count})

    @check_login
    def get_checkout_page_detail(self):
        """获取订单结算页面信息

        该方法会返回订单结算页面的详细信息：商品名称、价格、数量、库存状态等。

        :return: 结算信息 dict
        """
        url = 'http://trade.jd.com/shopping/order/getOrderInfo.action'
        # url = 'https://cart.jd.com/gotoOrder.action'
        payload = {
            'rid': str(int(time.time() * 1000)),
        }
        try:
            resp = self.sess.get(url=url, params=payload)
            if not response_status(resp):
                logger.error('获取订单结算页信息失败')
                return

            soup = BeautifulSoup(resp.text, "html.parser")
            self.risk_control = get_tag_value(soup.select('input#riskControl'), 'value')

            order_detail = {
                'address': soup.find('span', id='sendAddr').text[5:],  # remove '寄送至： ' from the begin
                'receiver': soup.find('span', id='sendMobile').text[4:],  # remove '收件人:' from the begin
                'total_price': soup.find('span', id='sumPayPriceId').text[1:],  # remove '￥' from the begin
                'items': []
            }
            # TODO: 这里可能会产生解析问题，待修复
            # for item in soup.select('div.goods-list div.goods-items'):
            #     div_tag = item.select('div.p-price')[0]
            #     order_detail.get('items').append({
            #         'name': get_tag_value(item.select('div.p-name a')),
            #         'price': get_tag_value(div_tag.select('strong.jd-price'))[2:],  # remove '￥ ' from the begin
            #         'num': get_tag_value(div_tag.select('span.p-num'))[1:],  # remove 'x' from the begin
            #         'state': get_tag_value(div_tag.select('span.p-state'))  # in stock or out of stock
            #     })

            logger.info("下单信息：%s", order_detail)
            return order_detail
        except Exception as e:
            logger.error('订单结算页面数据解析异常（可以忽略），报错信息：%s', e)

    def _save_invoice(self):
        """下单第三方商品时如果未设置发票，将从电子发票切换为普通发票

        http://jos.jd.com/api/complexTemplate.htm?webPamer=invoice&groupName=%E5%BC%80%E6%99%AE%E5%8B%92%E5%85%A5%E9%A9%BB%E6%A8%A1%E5%BC%8FAPI&id=566&restName=jd.kepler.trade.submit&isMulti=true

        :return:
        """
        url = 'https://trade.jd.com/shopping/dynamic/invoice/saveInvoice.action'
        data = {
            "invoiceParam.selectedInvoiceType": 1,
            "invoiceParam.companyName": "个人",
            "invoiceParam.invoicePutType": 0,
            "invoiceParam.selectInvoiceTitle": 4,
            "invoiceParam.selectBookInvoiceContent": "",
            "invoiceParam.selectNormalInvoiceContent": 1,
            "invoiceParam.vatCompanyName": "",
            "invoiceParam.code": "",
            "invoiceParam.regAddr": "",
            "invoiceParam.regPhone": "",
            "invoiceParam.regBank": "",
            "invoiceParam.regBankAccount": "",
            "invoiceParam.hasCommon": "true",
            "invoiceParam.hasBook": "false",
            "invoiceParam.consigneeName": "",
            "invoiceParam.consigneePhone": "",
            "invoiceParam.consigneeAddress": "",
            "invoiceParam.consigneeProvince": "请选择：",
            "invoiceParam.consigneeProvinceId": "NaN",
            "invoiceParam.consigneeCity": "请选择",
            "invoiceParam.consigneeCityId": "NaN",
            "invoiceParam.consigneeCounty": "请选择",
            "invoiceParam.consigneeCountyId": "NaN",
            "invoiceParam.consigneeTown": "请选择",
            "invoiceParam.consigneeTownId": 0,
            "invoiceParam.sendSeparate": "false",
            "invoiceParam.usualInvoiceId": "",
            "invoiceParam.selectElectroTitle": 4,
            "invoiceParam.electroCompanyName": "undefined",
            "invoiceParam.electroInvoiceEmail": "",
            "invoiceParam.electroInvoicePhone": "",
            "invokeInvoiceBasicService": "true",
            "invoice_ceshi1": "",
            "invoiceParam.showInvoiceSeparate": "false",
            "invoiceParam.invoiceSeparateSwitch": 1,
            "invoiceParam.invoiceCode": "",
            "invoiceParam.saveInvoiceFlag": 1
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://trade.jd.com/shopping/dynamic/invoice/saveInvoice.action',
        }
        self.sess.post(url=url, data=data, headers=headers)

    @check_login
    def submit_order(self):
        """提交订单

        重要：
        1.该方法只适用于普通商品的提交订单（即可以加入购物车，然后结算提交订单的商品）
        2.提交订单时，会对购物车中勾选✓的商品进行结算（如果勾选了多个商品，将会提交成一个订单）

        :return: True/False 订单提交结果
        """
        url = 'https://trade.jd.com/shopping/order/submitOrder.action'
        # js function of submit order is included in https://trade.jd.com/shopping/misc/js/order.js?r=2018070403091

        data = {
            'overseaPurchaseCookies': '',
            'vendorRemarks': '[]',
            'submitOrderParam.sopNotPutInvoice': 'false',
            'submitOrderParam.trackID': 'TestTrackId',
            'submitOrderParam.ignorePriceChange': '0',
            'submitOrderParam.btSupport': '0',
            'riskControl': self.risk_control,
            'submitOrderParam.isBestCoupon': 1,
            'submitOrderParam.jxj': 1,
            'submitOrderParam.trackId': self.track_id,  # Todo: need to get trackId
            'submitOrderParam.eid': self.eid,
            'submitOrderParam.fp': self.fp,
            'submitOrderParam.needCheck': 1,
        }

        # add payment password when necessary
        payment_pwd = global_config.get('account', 'payment_pwd')
        if payment_pwd:
            data['submitOrderParam.payPassword'] = encrypt_payment_pwd(payment_pwd)

        headers = {
            'User-Agent': self.user_agent,
            'Host': 'trade.jd.com',
            'Referer': 'http://trade.jd.com/shopping/order/getOrderInfo.action',
        }

        try:
            resp = self.sess.post(url=url, data=data, headers=headers)
            resp_json = json.loads(resp.text)

            # 返回信息示例：
            # 下单失败
            # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60123, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '请输入支付密码！'}
            # {'overSea': False, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'orderXml': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60017, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '您多次提交过快，请稍后再试'}
            # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60077, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '获取用户订单信息失败'}
            # {"cartXml":null,"noStockSkuIds":"xxx","reqInfo":null,"hasJxj":false,"addedServiceList":null,"overSea":false,"orderXml":null,"sign":null,"pin":"xxx","needCheckCode":false,"success":false,"resultCode":600157,"orderId":0,"submitSkuNum":0,"deductMoneyFlag":0,"goJumpOrderCenter":false,"payInfo":null,"scaleSkuInfoListVO":null,"purchaseSkuInfoListVO":null,"noSupportHomeServiceSkuList":null,"msgMobile":null,"addressVO":{"pin":"xxx","areaName":"","provinceId":xx,"cityId":xx,"countyId":xx,"townId":xx,"paymentId":0,"selected":false,"addressDetail":"xx","mobile":"xx","idCard":"","phone":null,"email":null,"selfPickMobile":null,"selfPickPhone":null,"provinceName":null,"cityName":null,"countyName":null,"townName":null,"giftSenderConsigneeName":null,"giftSenderConsigneeMobile":null,"gcLat":0.0,"gcLng":0.0,"coord_type":0,"longitude":0.0,"latitude":0.0,"selfPickOptimize":0,"consigneeId":0,"selectedAddressType":0,"siteType":0,"helpMessage":null,"tipInfo":null,"cabinetAvailable":true,"limitKeyword":0,"specialRemark":null,"siteProvinceId":0,"siteCityId":0,"siteCountyId":0,"siteTownId":0,"skuSupported":false,"addressSupported":0,"isCod":0,"consigneeName":null,"pickVOname":null,"shipmentType":0,"retTag":0,"tagSource":0,"userDefinedTag":null,"newProvinceId":0,"newCityId":0,"newCountyId":0,"newTownId":0,"newProvinceName":null,"newCityName":null,"newCountyName":null,"newTownName":null,"checkLevel":0,"optimizePickID":0,"pickType":0,"dataSign":0,"overseas":0,"areaCode":null,"nameCode":null,"appSelfPickAddress":0,"associatePickId":0,"associateAddressId":0,"appId":null,"encryptText":null,"certNum":null,"used":false,"oldAddress":false,"mapping":false,"addressType":0,"fullAddress":"xxxx","postCode":null,"addressDefault":false,"addressName":null,"selfPickAddressShuntFlag":0,"pickId":0,"pickName":null,"pickVOselected":false,"mapUrl":null,"branchId":0,"canSelected":false,"address":null,"name":"xxx","message":null,"id":0},"msgUuid":null,"message":"xxxxxx商品无货"}
            # {'orderXml': None, 'overSea': False, 'noStockSkuIds': 'xxx', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'cartXml': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 600158, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': {'oldAddress': False, 'mapping': False, 'pin': 'xxx', 'areaName': '', 'provinceId': xx, 'cityId': xx, 'countyId': xx, 'townId': xx, 'paymentId': 0, 'selected': False, 'addressDetail': 'xxxx', 'mobile': 'xxxx', 'idCard': '', 'phone': None, 'email': None, 'selfPickMobile': None, 'selfPickPhone': None, 'provinceName': None, 'cityName': None, 'countyName': None, 'townName': None, 'giftSenderConsigneeName': None, 'giftSenderConsigneeMobile': None, 'gcLat': 0.0, 'gcLng': 0.0, 'coord_type': 0, 'longitude': 0.0, 'latitude': 0.0, 'selfPickOptimize': 0, 'consigneeId': 0, 'selectedAddressType': 0, 'newCityName': None, 'newCountyName': None, 'newTownName': None, 'checkLevel': 0, 'optimizePickID': 0, 'pickType': 0, 'dataSign': 0, 'overseas': 0, 'areaCode': None, 'nameCode': None, 'appSelfPickAddress': 0, 'associatePickId': 0, 'associateAddressId': 0, 'appId': None, 'encryptText': None, 'certNum': None, 'addressType': 0, 'fullAddress': 'xxxx', 'postCode': None, 'addressDefault': False, 'addressName': None, 'selfPickAddressShuntFlag': 0, 'pickId': 0, 'pickName': None, 'pickVOselected': False, 'mapUrl': None, 'branchId': 0, 'canSelected': False, 'siteType': 0, 'helpMessage': None, 'tipInfo': None, 'cabinetAvailable': True, 'limitKeyword': 0, 'specialRemark': None, 'siteProvinceId': 0, 'siteCityId': 0, 'siteCountyId': 0, 'siteTownId': 0, 'skuSupported': False, 'addressSupported': 0, 'isCod': 0, 'consigneeName': None, 'pickVOname': None, 'shipmentType': 0, 'retTag': 0, 'tagSource': 0, 'userDefinedTag': None, 'newProvinceId': 0, 'newCityId': 0, 'newCountyId': 0, 'newTownId': 0, 'newProvinceName': None, 'used': False, 'address': None, 'name': 'xx', 'message': None, 'id': 0}, 'msgUuid': None, 'message': 'xxxxxx商品无货'}
            # 下单成功
            # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': True, 'resultCode': 0, 'orderId': 8740xxxxx, 'submitSkuNum': 1, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': None}

            if resp_json.get('success'):
                order_id = resp_json.get('orderId')
                logger.info('订单提交成功! 订单号：%s', order_id)
                if self.send_message:
                    self.messenger.send(text='jd-assistant 订单提交成功', desp='订单号：%s' % order_id)
                return True
            else:
                message, result_code = resp_json.get('message'), resp_json.get('resultCode')
                if result_code == 0:
                    self._save_invoice()
                    message = message + '(下单商品可能为第三方商品，将切换为普通发票进行尝试)'
                elif result_code == 60077:
                    message = message + '(可能是购物车为空 或 未勾选购物车中商品)'
                elif result_code == 60123:
                    message = message + '(需要在config.ini文件中配置支付密码)'
                logger.info('订单提交失败, 错误码：%s, 返回信息：%s', result_code, message)
                logger.info(resp_json)
                return False
        except Exception as e:
            logger.error(e)
            return False

    @check_login
    def submit_order_with_retry(self, retry=3, interval=4):
        """提交订单，并且带有重试功能
        :param retry: 重试次数
        :param interval: 重试间隔
        :return: 订单提交结果 True/False
        """
        for i in range(1, retry + 1):
            logger.info('第[%s/%s]次尝试提交订单', i, retry)
            self.get_checkout_page_detail()
            if self.submit_order():
                logger.info('第%s次提交订单成功', i)
                return True
            else:
                if i < retry:
                    logger.info('第%s次提交失败，%ss后重试', i, interval)
                    time.sleep(interval)
        else:
            logger.info('重试提交%s次结束', retry)
            return False

    @check_login
    def submit_order_by_time(self, buy_time, retry=4, interval=5):
        """定时提交商品订单

        重要：该方法只适用于普通商品的提交订单，事先需要先将商品加入购物车并勾选✓。

        :param buy_time: 下单时间，例如：'2018-09-28 22:45:50.000'
        :param retry: 下单重复执行次数，可选参数，默认4次
        :param interval: 下单执行间隔，可选参数，默认5秒
        :return:
        """
        t = Timer(buy_time=buy_time)
        t.start()

        for count in range(1, retry + 1):
            logger.info('第[%s/%s]次尝试提交订单', count, retry)
            if self.submit_order():
                break
            logger.info('休息%ss', interval)
            time.sleep(interval)
        else:
            logger.info('执行结束，提交订单失败！')

    @check_login
    def get_order_info(self, unpaid=True):
        """查询订单信息
        :param unpaid: 只显示未付款订单，可选参数，默认为True
        :return:
        """
        url = 'https://order.jd.com/center/list.action'
        payload = {
            'search': 0,
            'd': 1,
            's': 4096,
        }  # Orders for nearly three months
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://passport.jd.com/uc/login?ltype=logout',
        }

        try:
            resp = self.sess.get(url=url, params=payload, headers=headers)
            if not response_status(resp):
                logger.error('获取订单页信息失败')
                return
            soup = BeautifulSoup(resp.text, "html.parser")

            logger.info('************************订单列表页查询************************')
            order_table = soup.find('table', {'class': 'order-tb'})
            table_bodies = order_table.select('tbody')
            exist_order = False
            for table_body in table_bodies:
                # get order status
                order_status = get_tag_value(table_body.select('span.order-status')).replace("订单状态：", "")

                # check if order is waiting for payment
                # wait_payment = bool(table_body.select('a.btn-pay'))
                wait_payment = "等待付款" in order_status

                # only show unpaid orders if unpaid=True
                if unpaid and (not wait_payment):
                    continue

                exist_order = True

                # get order_time, order_id
                tr_th = table_body.select('tr.tr-th')[0]
                order_time = get_tag_value(tr_th.select('span.dealtime'))
                order_id = get_tag_value(tr_th.select('span.number a'))

                # get sum_price, pay_method
                sum_price = ''
                pay_method = ''
                amount_div = table_body.find('div', {'class': 'amount'})
                if amount_div:
                    spans = amount_div.select('span')
                    pay_method = get_tag_value(spans, index=1)
                    # if the order is waiting for payment, the price after the discount is shown.
                    sum_price = get_tag_value(amount_div.select('strong'), index=1)[1:] if wait_payment \
                        else get_tag_value(spans, index=0)[4:]

                # get name and quantity of items in order
                items_dict = dict()  # {'item_id_1': quantity_1, 'item_id_2': quantity_2, ...}
                tr_bds = table_body.select('tr.tr-bd')
                for tr_bd in tr_bds:
                    item = tr_bd.find('div', {'class': 'goods-item'})
                    if not item:
                        break
                    item_id = item.get('class')[1][2:]
                    quantity = get_tag_value(tr_bd.select('div.goods-number'))[1:]
                    items_dict[item_id] = quantity

                order_info_format = '下单时间:{0}----订单号:{1}----商品列表:{2}----订单状态:{3}----总金额:{4}元----付款方式:{5}'
                logger.info(order_info_format.format(order_time, order_id, parse_items_dict(items_dict), order_status,
                                                     sum_price, pay_method))

            if not exist_order:
                logger.info('订单查询为空')
        except Exception as e:
            logger.error(e)

    @deprecated
    def _get_seckill_url(self, sku_id):
        """获取商品的抢购链接

        点击"抢购"按钮后，会有两次302跳转，最后到达订单结算页面
        这里返回第一次跳转后的页面url，作为商品的抢购链接

        :param sku_id: 商品id
        :return: 商品的抢购链接
        """
        url = 'https://itemko.jd.com/itemShowBtn'
        payload = {
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            'skuId': sku_id,
            'from': 'pc',
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.user_agent,
            'Host': 'itemko.jd.com',
            'Referer': 'https://item.jd.com/{}.html'.format(sku_id),
        }
        retry_interval = 0.5

        while True:
            resp = self.sess.get(url=url, headers=headers, params=payload)
            resp_json = parse_json(resp.text)
            if resp_json.get('url'):
                # https://divide.jd.com/user_routing?skuId=8654289&sn=c3f4ececd8461f0e4d7267e96a91e0e0&from=pc
                router_url = 'https:' + resp_json.get('url')
                # https://marathon.jd.com/captcha.html?skuId=8654289&sn=c3f4ececd8461f0e4d7267e96a91e0e0&from=pc
                seckill_url = router_url.replace('divide', 'marathon').replace('user_routing', 'captcha.html')
                logger.info("抢购链接获取成功: %s", seckill_url)
                return seckill_url
            else:
                logger.info("抢购链接获取失败，%s不是抢购商品或抢购页面暂未刷新，%s秒后重试", sku_id, retry_interval)
                time.sleep(retry_interval)

    @deprecated
    def request_seckill_url(self, sku_id):
        """访问商品的抢购链接（用于设置cookie等）
        :param sku_id: 商品id
        :return:
        """
        if not self.seckill_url.get(sku_id):
            self.seckill_url[sku_id] = self._get_seckill_url(sku_id)
        headers = {
            'User-Agent': self.user_agent,
            'Host': 'marathon.jd.com',
            'Referer': 'https://item.jd.com/{}.html'.format(sku_id),
        }
        self.sess.get(url=self.seckill_url.get(sku_id), headers=headers, allow_redirects=False)

    @deprecated
    def request_seckill_checkout_page(self, sku_id, num=1):
        """访问抢购订单结算页面
        :param sku_id: 商品id
        :param num: 购买数量，可选参数，默认1个
        :return:
        """
        url = 'https://marathon.jd.com/seckill/seckill.action'
        payload = {
            'skuId': sku_id,
            'num': num,
            'rid': int(time.time())
        }
        headers = {
            'User-Agent': self.user_agent,
            'Host': 'marathon.jd.com',
            'Referer': 'https://item.jd.com/{}.html'.format(sku_id),
        }
        self.sess.get(url=url, params=payload, headers=headers)

    @deprecated
    def _get_seckill_init_info(self, sku_id, num=1):
        """获取秒杀初始化信息（包括：地址，发票，token）
        :param sku_id:
        :param num: 购买数量，可选参数，默认1个
        :return: 初始化信息组成的dict
        """
        url = 'https://marathon.jd.com/seckillnew/orderService/pc/init.action'
        data = {
            'sku': sku_id,
            'num': num,
            'isModifyAddress': 'false',
        }
        headers = {
            'User-Agent': self.user_agent,
            'Host': 'marathon.jd.com',
        }
        resp = self.sess.post(url=url, data=data, headers=headers)
        return parse_json(resp.text)

    @deprecated
    def _gen_seckill_order_data(self, sku_id, num=1):
        """生成提交抢购订单所需的请求体参数
        :param sku_id: 商品id
        :param num: 购买数量，可选参数，默认1个
        :return: 请求体参数组成的dict
        """

        # 获取用户秒杀初始化信息
        if not self.seckill_init_info.get(sku_id):
            self.seckill_init_info[sku_id] = self._get_seckill_init_info(sku_id)

        init_info = self.seckill_init_info.get(sku_id)
        default_address = init_info['addressList'][0]  # 默认地址dict
        invoice_info = init_info.get('invoiceInfo', {})  # 默认发票信息dict, 有可能不返回
        token = init_info['token']

        data = {
            'skuId': sku_id,
            'num': num,
            'addressId': default_address['id'],
            'yuShou': str(bool(int(init_info['seckillSkuVO']['extMap'].get('YuShou', '0')))).lower(),
            'isModifyAddress': 'false',
            'name': default_address['name'],
            'provinceId': default_address['provinceId'],
            'cityId': default_address['cityId'],
            'countyId': default_address['countyId'],
            'townId': default_address['townId'],
            'addressDetail': default_address['addressDetail'],
            'mobile': default_address['mobile'],
            'mobileKey': default_address['mobileKey'],
            'email': default_address.get('email', ''),
            'postCode': '',
            'invoiceTitle': invoice_info.get('invoiceTitle', -1),
            'invoiceCompanyName': '',
            'invoiceContent': invoice_info.get('invoiceContentType', 1),
            'invoiceTaxpayerNO': '',
            'invoiceEmail': '',
            'invoicePhone': invoice_info.get('invoicePhone', ''),
            'invoicePhoneKey': invoice_info.get('invoicePhoneKey', ''),
            'invoice': 'true' if invoice_info else 'false',
            'password': global_config.get('account', 'payment_pwd'),
            'codTimeType': 3,
            'paymentType': 4,
            'areaCode': '',
            'overseas': 0,
            'phone': '',
            'eid': self.eid,
            'fp': self.fp,
            'token': token,
            'pru': ''
        }
        return data

    @deprecated
    def submit_seckill_order(self, sku_id, num=1):
        """提交抢购（秒杀）订单
        :param sku_id: 商品id
        :param num: 购买数量，可选参数，默认1个
        :return: 抢购结果 True/False
        """
        url = 'https://marathon.jd.com/seckillnew/orderService/pc/submitOrder.action'
        payload = {
            'skuId': sku_id,
        }
        if not self.seckill_order_data.get(sku_id):
            self.seckill_order_data[sku_id] = self._gen_seckill_order_data(sku_id, num)

        headers = {
            'User-Agent': self.user_agent,
            'Host': 'marathon.jd.com',
            'Referer': 'https://marathon.jd.com/seckill/seckill.action?skuId={0}&num={1}&rid={2}'.format(
                sku_id, num, int(time.time())),
        }

        resp_json = None
        try:
            resp = self.sess.post(url=url, headers=headers, params=payload,
                                  data=self.seckill_order_data.get(sku_id), timeout=5)
            logger.info(resp.text)
            resp_json = parse_json(resp.text)
        except Exception as e:
            logger.error('秒杀请求出错：%s', str(e))
            return False
        # 返回信息
        # 抢购失败：
        # {'errorMessage': '很遗憾没有抢到，再接再厉哦。', 'orderId': 0, 'resultCode': 60074, 'skuId': 0, 'success': False}
        # {'errorMessage': '抱歉，您提交过快，请稍后再提交订单！', 'orderId': 0, 'resultCode': 60017, 'skuId': 0, 'success': False}
        # {'errorMessage': '系统正在开小差，请重试~~', 'orderId': 0, 'resultCode': 90013, 'skuId': 0, 'success': False}
        # 抢购成功：
        # {"appUrl":"xxxxx","orderId":820227xxxxx,"pcUrl":"xxxxx","resultCode":0,"skuId":0,"success":true,"totalMoney":"xxxxx"}

        if resp_json.get('success'):
            order_id = resp_json.get('orderId')
            total_money = resp_json.get('totalMoney')
            pay_url = 'https:' + resp_json.get('pcUrl')
            logger.info('抢购成功，订单号: %s, 总价: %s, 电脑端付款链接: %s', order_id, total_money, pay_url)
            return True
        else:
            logger.info('抢购失败，返回信息: %s', resp_json)
            return False

    @deprecated
    def exec_seckill(self, sku_id, retry=4, interval=4, num=1, fast_mode=True):
        """立即抢购

        抢购商品的下单流程与普通商品不同，不支持加入购物车，可能需要提前预约，主要执行流程如下：
        1. 访问商品的抢购链接
        2. 访问抢购订单结算页面（好像可以省略这步，待测试）
        3. 提交抢购（秒杀）订单

        :param sku_id: 商品id
        :param retry: 抢购重复执行次数，可选参数，默认4次
        :param interval: 抢购执行间隔，可选参数，默认4秒
        :param num: 购买数量，可选参数，默认1个
        :param fast_mode: 快速模式：略过访问抢购订单结算页面这一步骤，默认为 True
        :return: 抢购结果 True/False
        """
        for count in range(1, retry + 1):
            logger.info('第[%s/%s]次尝试抢购商品:%s', count, retry, sku_id)

            self.request_seckill_url(sku_id)
            if not fast_mode:
                self.request_seckill_checkout_page(sku_id, num)

            if self.submit_seckill_order(sku_id, num):
                return True
            else:
                logger.info('休息%ss', interval)
                time.sleep(interval)
        else:
            logger.info('执行结束，抢购%s失败！', sku_id)
            return False

    @deprecated
    def exec_seckill_by_time(self, sku_ids, buy_time, retry=4, interval=4, num=1, fast_mode=True):
        """定时抢购
        :param sku_ids: 商品id，多个商品id用逗号进行分割，如"123,456,789"
        :param buy_time: 下单时间，例如：'2018-09-28 22:45:50.000'
        :param retry: 抢购重复执行次数，可选参数，默认4次
        :param interval: 抢购执行间隔，可选参数，默认4秒
        :param num: 购买数量，可选参数，默认1个
        :param fast_mode: 快速模式：略过访问抢购订单结算页面这一步骤，默认为 True
        :return:
        """
        items_dict = parse_sku_id(sku_ids=sku_ids)
        logger.info('准备抢购商品:%s', list(items_dict.keys()))

        t = Timer(buy_time=buy_time)
        t.start()

        for sku_id in items_dict:
            logger.info('开始抢购商品:%s', sku_id)
            self.exec_seckill(sku_id, retry, interval, num, fast_mode)

    @check_login
    def exec_reserve_seckill_by_time(self, sku_id, buy_time, retry=4, interval=4, num=1):
        """定时抢购`预约抢购商品`

        预约抢购商品特点：
            1.需要提前点击预约
            2.大部分此类商品在预约后自动加入购物车，在购物车中可见但无法勾选✓，也无法进入到结算页面（重要特征）
            3.到了抢购的时间点后，才能勾选并结算下单

        注意：
            1.请在抢购开始前手动清空购物车中此类无法勾选的商品！（因为脚本在执行清空购物车操作时，无法清空不能勾选的商品）

        :param sku_id: 商品id
        :param buy_time: 下单时间，例如：'2018-09-28 22:45:50.000'
        :param retry: 抢购重复执行次数，可选参数，默认4次
        :param interval: 抢购执行间隔，可选参数，默认4秒
        :param num: 购买数量，可选参数，默认1个
        :return:
        """

        t = Timer(buy_time=buy_time)
        t.start()

        self.add_item_to_cart(sku_ids={sku_id: num})

        for count in range(1, retry + 1):
            logger.info('第[%s/%s]次尝试提交订单', count, retry)
            if self.submit_order():
                break
            logger.info('休息%ss', interval)
            time.sleep(interval)
        else:
            logger.info('执行结束，提交订单失败！')

    @check_login
    def buy_item_in_stock(self, sku_ids, area, wait_all=False, stock_interval=3, submit_retry=3, submit_interval=5):
        """根据库存自动下单商品
        :param sku_ids: 商品id。可以设置多个商品，也可以带数量，如：'1234' 或 '1234,5678' 或 '1234:2' 或 '1234:2,5678:3'
        :param area: 地区id
        :param wait_all: 是否等所有商品都有货才一起下单，可选参数，默认False
        :param stock_interval: 查询库存时间间隔，可选参数，默认3秒
        :param submit_retry: 提交订单失败后重试次数，可选参数，默认3次
        :param submit_interval: 提交订单失败后重试时间间隔，可选参数，默认5秒
        :return:
        """
        items_dict = parse_sku_id(sku_ids)
        items_list = list(items_dict.keys())
        area_id = parse_area_id(area=area)

        if not wait_all:
            logger.info('下单模式：%s 任一商品有货并且未下架均会尝试下单', items_list)
            while True:
                for (sku_id, count) in items_dict.items():
                    if not self.if_item_can_be_ordered(sku_ids={sku_id: count}, area=area_id):
                        logger.info('%s 不满足下单条件，%ss后进行下一次查询', sku_id, stock_interval)
                    else:
                        logger.info('%s 满足下单条件，开始执行', sku_id)
                        self._cancel_select_all_cart_item()
                        self._add_or_change_cart_item(self.get_cart_detail(), sku_id, count)
                        if self.submit_order_with_retry(submit_retry, submit_interval):
                            return

                    time.sleep(stock_interval)
        else:
            logger.info('下单模式：%s 所有都商品同时有货并且未下架才会尝试下单', items_list)
            while True:
                if not self.if_item_can_be_ordered(sku_ids=sku_ids, area=area_id):
                    logger.info('%s 不满足下单条件，%ss后进行下一次查询', items_list, stock_interval)
                else:
                    logger.info('%s 满足下单条件，开始执行', items_list)
                    self._cancel_select_all_cart_item()
                    shopping_cart = self.get_cart_detail()
                    for (sku_id, count) in items_dict.items():
                        self._add_or_change_cart_item(shopping_cart, sku_id, count)

                    if self.submit_order_with_retry(submit_retry, submit_interval):
                        return

                time.sleep(stock_interval)
