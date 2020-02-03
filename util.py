#!/usr/bin/env python
# -*- coding:utf-8 -*-
import functools
import json
import os
import re
import warnings
from base64 import b64encode

import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5

from log import logger

RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDC7kw8r6tq43pwApYvkJ5lalja
N9BZb21TAIfT/vexbobzH7Q8SUdP5uDPXEBKzOjx2L28y7Xs1d9v3tdPfKI2LR7P
AzWBmDMn8riHrDDNpUpJnlAGUqJG9ooPn8j7YNpcxCa1iybOlc2kEhmJn5uwoanQ
q+CA6agNkqly2H4j6wIDAQAB
-----END PUBLIC KEY-----"""

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'

DEFAULT_EID = 'D5GZVU5ZO5VBUFMLOUHMNHK2BXXVKI4ZQK3JKCOIB4PRERKTQXV3BNSG557BQLPVVT4ZN3NKVSXAKTVPJXDEPEBDGU'

DEFAULT_FP = '18c7d83a053e6bbb51f755aea595bbb8'

DEFAULT_TRACK_ID = '9643cbd55bbbe103eef18a213e069eb0'


def encrypt_pwd(password, public_key=RSA_PUBLIC_KEY):
    rsa_key = RSA.importKey(public_key)
    encryptor = Cipher_pkcs1_v1_5.new(rsa_key)
    cipher = b64encode(encryptor.encrypt(password.encode('utf-8')))
    return cipher.decode('utf-8')


def encrypt_payment_pwd(payment_pwd):
    return ''.join(['u3' + x for x in payment_pwd])


def response_status(resp):
    if resp.status_code != requests.codes.OK:
        print('Status: %u, Url: %s' % (resp.status_code, resp.url))
        return False
    return True


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


def parse_items_dict(d):
    result = ''
    for index, key in enumerate(d):
        if index < len(d) - 1:
            result = result + '{0} x {1}, '.format(key, d[key])
        else:
            result = result + '{0} x {1}'.format(key, d[key])
    return result


def parse_sku_id(sku_ids):
    """将商品id字符串解析为字典

    商品id字符串采用英文逗号进行分割。
    可以在每个id后面用冒号加上数字，代表该商品的数量，如果不加数量则默认为1。

    例如：
    输入  -->  解析结果
    '123456' --> {'123456': '1'}
    '123456,123789' --> {'123456': '1', '123789': '1'}
    '123456:1,123789:3' --> {'123456': '1', '123789': '3'}
    '123456:2,123789' --> {'123456': '2', '123789': '1'}

    :param sku_ids: 商品id字符串
    :return: dict
    """
    if isinstance(sku_ids, dict):  # 防止重复解析
        return sku_ids

    sku_id_list = list(filter(bool, map(lambda x: x.strip(), sku_ids.split(','))))
    result = dict()
    for item in sku_id_list:
        if ':' in item:
            sku_id, count = map(lambda x: x.strip(), item.split(':'))
            result[sku_id] = count
        else:
            result[item] = '1'
    return result


def parse_area_id(area):
    """解析地区id字符串：将分隔符替换为下划线 _
    :param area: 地区id字符串（使用 _ 或 - 进行分割），如 12_904_3375 或 12-904-3375
    :return: 解析后字符串
    """
    return area.replace('-', '_')


def split_area_id(area_id):
    """将地区id字符串按照下划线进行切割，构成数组。数组长度不满4位则用'0'进行填充。
    :param area_id: 地区id字符串（使用 _ 或 - 进行分割），如 12_904_3375 或 12-904-3375
    :return: list
    """
    area = re.split('_|-', area_id)
    area.extend((4 - len(area)) * ['0'])
    return area


def deprecated(func):
    """This decorator is used to mark functions as deprecated.
    It will result in a warning being emitted when the function is used.
    """

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn(
            "Call to deprecated function {}.".format(func.__name__),
            category=DeprecationWarning,
            stacklevel=2
        )
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)

    return new_func


def check_login(func):
    """用户登陆态校验装饰器。若用户未登陆，则调用扫码登陆"""

    @functools.wraps(func)
    def new_func(self, *args, **kwargs):
        if not self.is_login:
            logger.info("{0} 需登陆后调用，开始扫码登陆".format(func.__name__))
            self.login_by_QRcode()
        return func(self, *args, **kwargs)

    return new_func
