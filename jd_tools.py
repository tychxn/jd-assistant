#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import time
import json
from base64 import b64encode
from random import shuffle

import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5

RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDC7kw8r6tq43pwApYvkJ5lalja
N9BZb21TAIfT/vexbobzH7Q8SUdP5uDPXEBKzOjx2L28y7Xs1d9v3tdPfKI2LR7P
AzWBmDMn8riHrDDNpUpJnlAGUqJG9ooPn8j7YNpcxCa1iybOlc2kEhmJn5uwoanQ
q+CA6agNkqly2H4j6wIDAQAB
-----END PUBLIC KEY-----"""

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'

DEFAULT_EID = 'D5GZVU5ZO5VBUFMLOUHMNHK2BXXVKI4ZQK3JKCOIB4PRERKTQXV3BNSG557BQLPVVT4ZN3NKVSXAKTVPJXDEPEBDGU'

DEFAULT_FP = '18c7d83a053e6bbb51f755aea595bbb8'


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


def parse_items_dict(d):
    result = ''
    for index, key in enumerate(d):
        if index < len(d) - 1:
            result = result + '{0} x {1}, '.format(key, d[key])
        else:
            result = result + '{0} x {1}'.format(key, d[key])
    return result


def parse_sku_id(sku_ids, contain_count=False, need_shuffle=False):
    sku_id_list = list(map(lambda x: x.strip(), sku_ids.split(',')))
    sku_id_list = list(filter(bool, sku_id_list))  # remove empty

    if contain_count or (':' in sku_ids):
        sku_id_dict = dict()
        for item in sku_id_list:
            sku_id, count = map(lambda x: x.strip(), item.split(':'))
            sku_id_dict[sku_id] = count
        return sku_id_dict

    if need_shuffle:
        shuffle(sku_id_list)
    return sku_id_list


def list_to_str(l):
    return '[%s]' % ','.join(l)


def parse_area_id(area_id='12_904_3375'):
    area = list(area_id.split('_'))
    area.extend((4 - len(area)) * ['0'])
    return area
