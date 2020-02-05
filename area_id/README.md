# 地址id如何获取？

## 方法一

在本文件夹中根据地址查询对应的文件。

## 方法二

在商品页面(例如 https://item.jd.com/1178879.html) 打开开发者工具，在 Console 中执行以下 Javascript 代码：

```js
var el = document.getElementsByClassName("ui-area-text")[0]
var area_name = el.getAttribute("title")
var area_id = el.getAttribute("data-id").replace(/-/g, "_")
console.log(area_name)
console.log(area_id)
```

## 方法三

运行本文件夹中的 Python 脚本，根据提示逐级选择区域。感谢 @6r6 提供脚本～

```sh
python get_area_id.py
```
