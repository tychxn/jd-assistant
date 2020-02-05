#!/usr/bin/env python
# -*- coding:utf-8 -*-

import requests
import json

province = [{'name': '北京', 'value': 1}, {'name': '上海', 'value': 2}, {'name': '天津', 'value': 3}, {'name': '重庆', 'value': 4}, {'name': '河北', 'value': 5}, {'name': '山西', 'value': 6}, {'name': '河南', 'value': 7}, {'name': '辽宁', 'value': 8}, {'name': '吉林', 'value': 9}, {'name': '黑龙江', 'value': 10}, {'name': '内蒙古', 'value': 11}, {'name': '江苏', 'value': 12}, {'name': '山东', 'value': 13}, {'name': '安徽', 'value': 14}, {'name': '浙江', 'value': 15}, {'name': '福建', 'value': 16}, {'name': '湖北', 'value': 17}, {'name': '湖南', 'value': 18}, {'name': '广东', 'value': 19}, {'name': '广西', 'value': 20}, {'name': '江西', 'value': 21}, {'name': '四川', 'value': 22}, {'name': '海南', 'value': 23}, {'name': ' 贵州', 'value': 24}, {'name': '云南', 'value': 25}, {'name': '西藏', 'value': 26}, {'name': '陕西', 'value': 27}, {'name': '甘肃', 'value': 28}, {'name': '青海', 'value': 29}, {'name': '宁夏', 'value': 30}, {'name': '新疆', 'value': 31}, {'name': '台湾', 'value': 32}, {'name': '港澳', 'value': 52993}]

def get_by_fid(fid):
    base_uri = 'https://d.jd.com/area/get'
    payload = {'fid':fid}
    headers = {'Referer':'https://www.jd.com/','User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.132 Safari/536.36 Edg/80.0.309.71'}
    resp = requests.get(url=base_uri,params=payload,headers=headers)
    resp_list = json.loads(resp.text)
    return resp_list

if __name__ == '__main__':
    for loc in province:
        print('{} 对应的编号为 {}'.format(loc['name'],loc['value']))
    print('-------------------------------------------------')
    fid1 = input('请继续输入省份编号：')
    city_list = get_by_fid(fid1)
    for loc in city_list:
        print('{} 对应的编号为 {}'.format(loc['name'],loc['id']))
    print('-------------------------------------------------')
    fid2=input('请继续输入市编号：')
    district_list = get_by_fid(fid2)
    for loc in district_list:
        print('{} 对应的编号为 {}'.format(loc['name'],loc['id']))
    print('-------------------------------------------------')
    fid3=input('请继续输入县镇编号：')
    street_list = get_by_fid(fid3)
    if street_list == []:
        print('您选择的最终的区域id为：{}_{}_{}'.format(fid1,fid2,fid3))
        exit()
    else:
        for loc in street_list:
            print('{} 对应的编号为 {}'.format(loc['name'],loc['id']))
    fid4 = input('请继续输入街道编号：')
    print('-------------------------------------------------')
    print('您选择的最终的区域id为：{}_{}_{}_{}'.format(fid1,fid2,fid3,fid4))
    
