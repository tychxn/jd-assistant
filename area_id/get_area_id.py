# !/usr/bin/env python
# -*- coding:utf-8 -*-

"""
area参数自助生成
运行脚本，根据提示逐级选择区域即可
"""

import json

import requests

provinces = [
    {'name': '北京', 'id': 1}, {'name': '上海', 'id': 2}, {'name': '天津', 'id': 3},
    {'name': '重庆', 'id': 4}, {'name': '河北', 'id': 5}, {'name': '山西', 'id': 6},
    {'name': '河南', 'id': 7}, {'name': '辽宁', 'id': 8}, {'name': '吉林', 'id': 9},
    {'name': '黑龙江', 'id': 10}, {'name': '内蒙古', 'id': 11}, {'name': '江苏', 'id': 12},
    {'name': '山东', 'id': 13}, {'name': '安徽', 'id': 14}, {'name': '浙江', 'id': 15},
    {'name': '福建', 'id': 16}, {'name': '湖北', 'id': 17}, {'name': '湖南', 'id': 18},
    {'name': '广东', 'id': 19}, {'name': '广西', 'id': 20}, {'name': '江西', 'id': 21},
    {'name': '四川', 'id': 22}, {'name': '海南', 'id': 23}, {'name': '贵州', 'id': 24},
    {'name': '云南', 'id': 25}, {'name': '西藏', 'id': 26}, {'name': '陕西', 'id': 27},
    {'name': '甘肃', 'id': 28}, {'name': '青海', 'id': 29}, {'name': '宁夏', 'id': 30},
    {'name': '新疆', 'id': 31}, {'name': '台湾', 'id': 32}, {'name': '港澳', 'id': 52993},
    {'name': '钓鱼岛', 'id': 84}
]


def get_area_by_id(_id):
    base_uri = 'https://d.jd.com/area/get'
    payload = {'fid': _id}
    resp = requests.get(url=base_uri, params=payload)
    return json.loads(resp.text)


def print_area(area_list):
    for area in area_list:
        print('【{}】 {}'.format(area['id'], area['name']))
    print('-------------------------------------------------')


def select_area(area_list):
    while True:
        user_input = input('请继续输入编号：').strip()
        selected_area = [area for area in area_list if str(area['id']) == user_input or area['name'] == user_input]
        if not selected_area:
            print('编号错误，请重新输入')
            continue
        print('已选择：{}'.format(selected_area[0]['name']))
        return selected_area[0]


def main():
    print_area(provinces)
    province = select_area(provinces)

    cities = get_area_by_id(province['id'])
    print_area(cities)
    city = select_area(cities)

    districts = get_area_by_id(city['id'])
    print_area(districts)
    district = select_area(districts)

    streets = get_area_by_id(district['id'])
    if not streets:
        print(
            '您选择的区域为：{}-{}-{}，id：{}_{}_{}'.format(
                province['name'], city['name'], district['name'],
                province['id'], city['id'], district['id']
            )
        )
        return

    print_area(streets)
    street = select_area(streets)
    print(
        '您选择的区域为：{}-{}-{}-{}，id：{}_{}_{}_{}'.format(
            province['name'], city['name'], district['name'], street['name'],
            province['id'], city['id'], district['id'], street['id']
        )
    )


if __name__ == '__main__':
    main()
