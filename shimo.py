#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
    提交数据到石墨文档
"""
from util import response_status
import requests

def shimo(content):
   """提交数据到石墨文档表单收集器
   """
   # 石墨文档提交数据格式
   data = {
      "duration" : 55,
      "formRev" : 1,
      "responseContent" : [
         {
            "guid" : "xxxxx",   #石墨文档的guid
            "text" : {
               "content" : "xxxxxxxx"
            },
            "type" : 0
         }
      ],
      "userFinger" : "-1",
      "userName" : "JD"
   }

   url = "https://shimo.im/api/newforms/forms/xpVxJQJjT3GJ8WhJ/submit"

   data['duration'] = 50
   data['responseContent'][0]['text']['content'] = content
   data['userName'] = "JD助手"
   # print("Duration: ", data['duration'])
   # print("userName: ",data['userName'])
   # print("Content: ", data['responseContent'][0]['text']['content'])
   # print(data)

   response = requests.post(url, json=data)  #用post方式提交数据
   if response.status_code == 200 or 204:
      #print(response.status_code)
      return True
   else:
      return False

if __name__ == '__main__':
   vercode = ['7102298241802','1369696304672','5557372871652']
   for x in vercode:
      shimo(x)
      # ok = shimo(x)
      # print(ok)