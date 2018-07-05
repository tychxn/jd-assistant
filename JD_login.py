#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import time
import json
import random
from base64 import b64encode

import requests
import pickle
from bs4 import BeautifulSoup
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5

rsa_public_key = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDC7kw8r6tq43pwApYvkJ5lalja
N9BZb21TAIfT/vexbobzH7Q8SUdP5uDPXEBKzOjx2L28y7Xs1d9v3tdPfKI2LR7P
AzWBmDMn8riHrDDNpUpJnlAGUqJG9ooPn8j7YNpcxCa1iybOlc2kEhmJn5uwoanQ
q+CA6agNkqly2H4j6wIDAQAB
-----END PUBLIC KEY-----"""


def encrypt_pwd(password, public_key=rsa_public_key):
    rsakey = RSA.importKey(public_key)
    encryptor = Cipher_pkcs1_v1_5.new(rsakey)
    cipher = b64encode(encryptor.encrypt(password.encode('utf-8')))
    return cipher.decode('utf-8')


def response_status(resp):
    if resp.status_code != requests.codes.OK:
        print('Status: %u, Url: %s' % (resp.status_code, resp.url))
        return False
    return True


def get_current_time():
    return time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())


def open_image(image_file):
    if os.name == "nt":
        os.system('start ' + image_file)  # for Windows
    else:
        if os.uname()[0] == "Linux":
            os.system("eog " + image_file)  # for Linux
        else:
            os.system("open " + image_file)  # for Mac


def save_image(resp, image_file):
    with open(image_file, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=1024):
            f.write(chunk)


def parse_json(s):
    begin = s.find('{')
    end = s.rfind('}') + 1
    return json.loads(s[begin:end])


def get_tag_value(tag, key='', index=0):
    if key:
        value = tag[index].get(key)
    else:
        value = tag[index].text
    return value.strip(' \t\r\n')


class JDlogin(object):

    def __init__(self):
        self.headers = {
            'Host': 'passport.jd.com',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.sess = requests.session()
        try:
            self._load_cookies()
        except Exception as e:
            pass

    def _load_cookies(self, cookies_file='cookies'):
        with open(cookies_file, 'rb') as f:
            cookies = pickle.load(f)
            self.sess.cookies.update(cookies)
            # Todo: need to validate whether cookies is expired

    def _save_cookies(self, cookies_file='cookies'):
        with open(cookies_file, 'wb') as f:
            pickle.dump(self.sess.cookies, f)

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
            print('获取是否需要验证码失败')
            return False

        js = json.loads(resp.text[1:-1])
        return js['verifycode']

    def _get_auth_code(self, uuid):
        image_file = os.path.join(os.getcwd(), 'JD_authcode.jpg')

        url = 'https://authcode.jd.com/verify/image'
        payload = {
            'a': 1,
            'acid': uuid,
            'uid': uuid,
            'yys': str(int(time.time() * 1000)),
        }
        self.headers['Host'] = 'authcode.jd.com'
        self.headers['Referer'] = 'https://passport.jd.com/uc/login'
        resp = self.sess.get(url, params=payload, headers=self.headers)

        if not response_status(resp):
            print('获取验证码失败')
            return ''

        save_image(resp, image_file)
        open_image(image_file)
        return input('验证码:')

    def _get_login_page(self):
        url = "https://passport.jd.com/new/login.aspx"
        page = self.sess.get(url, headers=self.headers)
        return page

    def _get_login_data(self):
        page = self._get_login_page()
        soup = BeautifulSoup(page.text, "html.parser")
        input_list = soup.select('.form input')

        data = dict()
        data['sa_token'] = input_list[0]['value']
        data['uuid'] = input_list[1]['value']
        data['_t'] = input_list[4]['value']
        data['loginType'] = input_list[5]['value']
        data['pubKey'] = input_list[7]['value']
        data['eid'] = 'UHU6KVDJS7PNLJUHG2ICBFACVLMEXVPQUGIK2QVXYMSN45BIEMUSICVLTYQYOZYZN2KWHV3WQWMFH4QPED2DVQHUXE'
        data['fp'] = '536e2679b85ddea9baccc7b705f2f8e0'
        return data

    def login_by_username(self, username, password):
        data = self._get_login_data()
        uuid = data['uuid']

        auth_code = ''
        if self._need_auth_code(username):
            print(get_current_time(), '本次登录需要验证码')
            auth_code = self._get_auth_code(uuid)
        else:
            print(get_current_time(), '本次登录不需要验证码')

        login_url = "https://passport.jd.com/uc/loginService"
        payload = {
            'uuid': uuid,
            'version': 2015,
            'r': random.random(),
        }
        data['authcode'] = auth_code
        data['loginname'] = username
        data['nloginpwd'] = encrypt_pwd(password)
        self.headers['Host'] = 'passport.jd.com'
        self.headers['Origin'] = 'https://passport.jd.com'
        self.headers['X-Requested-With'] = 'XMLHttpRequest'
        resp = self.sess.post(url=login_url, data=data, headers=self.headers, params=payload)

        if not response_status(resp):
            print(get_current_time(), '登录失败')
            return False

        if not self._get_login_result(resp):
            return False
        self._save_cookies()
        return True

    def _get_login_result(self, resp):
        result = resp.text
        if "success" in result:
            print(get_current_time(), '登录成功')
            return True
        else:
            js = json.loads(result[1:-1])
            js.pop('_t', None)
            print(get_current_time(), '登录失败 '+ list(js.values())[0])
            return False

    def _get_QRcode(self):
        url = 'https://qr.m.jd.com/show'
        self.headers['Host'] = 'qr.m.jd.com'
        self.headers['Referer'] = 'https://passport.jd.com/new/login.aspx'
        payload = {
            'appid': 133,
            'size': 147,
            't': str(int(time.time() * 1000)),
        }
        resp = self.sess.get(url=url, headers=self.headers, params=payload)

        if not response_status(resp):
            print(get_current_time(), '获取二维码失败')
            return False

        QRCode_file = 'QRcode.png'
        save_image(resp, QRCode_file)
        print(get_current_time(), '验证码获取成功，请打开京东APP扫描')
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
        resp = self.sess.get(url=url, headers=self.headers, params=payload)

        if not response_status(resp):
            print(get_current_time(), '获取二维码扫描结果出错')
            return False

        js = parse_json(resp.text)
        if js['code'] != 200:
            print(get_current_time(), 'Code: {0}, Message: {1}'.format(js['code'], js['msg']))
            return None
        else:
            print(get_current_time(), '已完成手机客户端确认')
            return js['ticket']

    def _validate_QRcode_ticket(self, ticket):
        url = 'https://passport.jd.com/uc/qrCodeTicketValidation'
        self.headers['Host'] = 'passport.jd.com'
        self.headers['Referer'] = 'https://passport.jd.com/uc/login?ltype=logout'
        resp = self.sess.get(url=url, headers=self.headers, params={'t': ticket})

        if not response_status(resp):
            return False

        js = json.loads(resp.text)
        if js['returnCode'] == 0:
            return True
        else:
            print(get_current_time(), js)
            return False

    def login_by_QRcode(self):
        self._get_login_page()

        # download QR code
        if not self._get_QRcode():
            print(get_current_time(), '登录失败')
            return False

        # get QR code ticket
        ticket = None
        retry_times = 90
        for _ in range(retry_times):
            ticket = self._get_QRcode_ticket()
            if ticket:
                break
            time.sleep(2)
        else:
            print(get_current_time(), '二维码扫描出错')
            return False

        # validate QR code ticket
        if not self._validate_QRcode_ticket(ticket):
            print(get_current_time(), '二维码登录失败')
            return False
        else:
            print(get_current_time(), '二维码登录成功')
            self._save_cookies()
            return True

    def _get_item_detail_page(self, sku_id):
        url = 'https://item.jd.com/{}.html'.format(sku_id)
        self.headers['Host'] = 'item.jd.com'
        page = self.sess.get(url=url, headers=self.headers)
        return page

    def get_item_stock_state(self, sku_id='862576', area='3_51035_39620_0'):
        page = self._get_item_detail_page(sku_id)
        m = re.search(r'cat: \[(.*?)\]', page.text)
        cat = m.group(1)

        url = 'https://c0.3.cn/stock'
        payload = {
            'skuId': sku_id,
            'buyNum': 1,
            'area': area,
            'ch': 1,
            '_': str(int(time.time() * 1000)),
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            'extraParam': '{"originid":"1"}',  # get error stock state without this param
            'cat': cat,  # get 403 Forbidden without this param (obtained from the detail page)
            # 'venderId': ''  # won't return seller information without this param (can be ignored)
        }
        self.headers['Host'] = 'c0.3.cn'
        self.headers['Referer'] = 'https://item.jd.com/{}.html'.format(sku_id)
        resp = requests.get(url=url, params=payload, headers=self.headers)

        js = parse_json(resp.text)
        stock_state = js['stock']['StockState']  # 33 -- in stock  34 -- out of stock
        stock_state_name = js['stock']['StockStateName']
        return stock_state, stock_state_name

    def get_item_price(self, sku_id='862576'):
        url = 'http://p.3.cn/prices/mgets'
        payload = {
            'type': 1,
            'pduid': int(time.time() * 1000),
            'skuIds': 'J_' + sku_id,
        }
        resp = self.sess.get(url=url, params=payload)
        js = parse_json(resp.text)
        return js['p']

    def add_item_to_cart(self, sku_id='862576', count=1):
        url = 'https://cart.jd.com/gate.action'
        payload = {
            'pid': sku_id,
            'pcount': count,
            'ptype': 1,
        }
        try:
            resp = self.sess.get(url=url, params=payload)
            soup = BeautifulSoup(resp.text, "html.parser")
            tag = soup.select('h3.ftx-02')  # [<h3 class="ftx-02">商品已成功加入购物车！</h3>]
            if not tag:
                print(get_current_time(), '{}添加到购物车失败'.format(sku_id))
                return False
            print(get_current_time(), '{}已成功加入购物车'.format(sku_id))
            return True
        except Exception as e:
            print(get_current_time(), e)
            return False

    def clear_cart(self):
        url = 'https://cart.jd.com/batchRemoveSkusFromCart.action'
        data = {
            'null': 0,
            't': 0,
            'outSkus': '',
            'random': random.random(),
        }
        try:
            resp = self.sess.post(url=url, data=data)
            # js = parse_json(resp.text)
            if not response_status(resp):
                print(get_current_time(), '购物车清空失败')
                return False
            print(get_current_time(), '购物车清空成功')
            return True
        except Exception as e:
            print(get_current_time(), e)
            return False

    def get_cart_detail(self):
        url = 'https://cart.jd.com/cart.action'
        cart_detail_format = '商品名称:{0}----单价:{1}----数量:{2}----总价:{3}'
        try:
            resp = self.sess.get(url)
            if not response_status(resp):
                print(get_current_time(), '获取购物车信息失败')
                return
            soup = BeautifulSoup(resp.text, "html.parser")

            print('************************购物车商品详情************************')
            for item in soup.select('div.item-form'):
                name = get_tag_value(item.select('div.p-name a'))
                price = get_tag_value(item.select('div.p-price strong'))
                quantity = get_tag_value(item.select('div.quantity-form input'), 'value')
                total_price = get_tag_value(item.select('div.p-sum strong'))
                print(cart_detail_format.format(name, price, quantity, total_price))
        except Exception as e:
            print(get_current_time(), e)

    def get_checkout_page_detail(self):
        url = 'http://trade.jd.com/shopping/order/getOrderInfo.action'
        # url = 'https://cart.jd.com/gotoOrder.action'
        payload = {
            'rid': str(int(time.time() * 1000)),
        }
        try:

            resp = self.sess.get(url=url, params=payload)
            if not response_status(resp):
                print(get_current_time(), '获取订单结算页信息失败')
                return
            soup = BeautifulSoup(resp.text, "html.parser")

            print('************************订单结算页详情************************')
            items = soup.select('div.goods-list div.goods-items')[1:]
            checkout_item_detail = '商品名称:{0}----单价:{1}----数量:{2}----库存:{3}'
            for item in items:
                name = get_tag_value(item.select('div.p-name a'))
                div_tag = item.select('div.p-price')[0]
                price = get_tag_value(div_tag.select('strong.jd-price'))[2:]  # remove '￥ ' from the begin of price
                quantity = get_tag_value(div_tag.select('span.p-num'))[1:]  # remove 'x' from the begin of quantity
                state = get_tag_value(div_tag.select('span.p-state'))  # in stock or out of stock
                print(checkout_item_detail.format(name, price, quantity, state))

            sum_price = soup.find('span', id='sumPayPriceId').text[1:]  # remove '￥' from the begin of sum price
            address = soup.find('span', id='sendAddr').text[5:]  # remove '收件人:' from the begin of receiver
            receiver = soup.find('span', id='sendMobile').text[4:]  # remove '寄送至： ' from the begin of address
            print('应付总额:{0}'.format(sum_price))
            print('收货地址:{0}----收件人:{1}'.format(address, receiver))
        except Exception as e:
            print(get_current_time(), e)


if __name__ == '__main__':
    # username = input('Username:')
    # password = input('Password:')
    jd = JDlogin()
    # jd.login_by_username(username, password)
    # jd.login_by_QRcode()
    print(jd.get_item_stock_state(sku_id='5089267'))
    print(jd.get_item_price(sku_id='5089267'))
    jd.add_item_to_cart(sku_id='5089267')
    # jd.clear_cart()
    jd.get_cart_detail()
    jd.get_checkout_page_detail()
