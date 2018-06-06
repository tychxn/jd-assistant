#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
import json
import random
from base64 import b64encode

import requests
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
    return time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime())


def open_image(image_file):
    if os.name == "nt":
        os.system('start ' + image_file)  # for Windows
    else:
        if os.uname()[0] == "Linux":
            os.system("eog " + image_file)  # for Linux
        else:
            os.system("open " + image_file)  # for Mac


class JDlogin(object):

    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.sess = requests.session()
        self.headers = {
            'Host': 'passport.jd.com',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def _need_auth_code(self, username):
        url = 'https://passport.jd.com/uc/showAuthCode'
        data = {
            'loginName' : username,
        }
        payload = {
            'version' : 2015,
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
            'a' : 1,
            'acid' : uuid,
            'uid' : uuid,
            'yys' : str(int(time.time() * 1000)),
        }
        self.headers['Host'] = 'authcode.jd.com'
        self.headers['Referer'] = 'https://passport.jd.com/uc/login'
        resp = self.sess.get(url, params=payload, headers=self.headers)

        if not response_status(resp):
            print('获取验证码失败')
            return False

        with open (image_file, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024):
                f.write(chunk)
        open_image(image_file)
        return input('验证码:')

    def _get_login_data(self):
        home_url = "https://passport.jd.com/new/login.aspx"
        page = self.sess.get(home_url, headers=self.headers)
        soup = BeautifulSoup(page.text, "html.parser")
        input_list = soup.select('.form input')

        data = {}
        data['sa_token'] = input_list[0]['value']
        data['uuid'] = input_list[1]['value']
        data['_t'] = input_list[4]['value']
        data['loginType'] = input_list[5]['value']
        data['pubKey'] = input_list[7]['value']
        data['eid'] = 'UHU6KVDJS7PNLJUHG2ICBFACVLMEXVPQUGIK2QVXYMSN45BIEMUSICVLTYQYOZYZN2KWHV3WQWMFH4QPED2DVQHUXE'
        data['fp'] = '536e2679b85ddea9baccc7b705f2f8e0'
        return data

    def login(self):
        data = self._get_login_data()

        auth_code = ''
        if self._need_auth_code(self.username):
            print(get_current_time(), '本次登录需要验证码')
            auth_code = self._get_auth_code(data['uuid'])
        else:
            print(get_current_time(), '本次登录不需要验证码')

        login_url = "https://passport.jd.com/uc/loginService"
        payload = {
            'uuid' : data['uuid'],
            'version': 2015,
            'r': random.random(),
        }
        data['authcode'] = auth_code
        data['loginname'] = self.username
        data['nloginpwd'] = encrypt_pwd(self.password)
        self.headers['Host'] = 'passport.jd.com'
        self.headers['Origin'] = 'https://passport.jd.com'
        self.headers['X-Requested-With'] = 'XMLHttpRequest'
        resp = self.sess.post(login_url, data=data, headers=self.headers, params=payload)

        if not response_status(resp):
            print('登录失败')
            return False

        if not self._get_login_result(resp):
            return False
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


if __name__ == '__main__':
    username = input('Username:')
    password = input('Password:')
    jd = JDlogin(username, password)
    jd.login()
