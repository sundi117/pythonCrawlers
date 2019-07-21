#!/usr/bin/env python3
# _*_ coding:utf-8 _*_
#
# @Desc    : 爱情动作XXX网站爬虫  https://www.100sht.space/
# @Author  : wangshengsheng
# @Time    : 2019/7/21 11:02
# @Version : 0.1


import requests
from lxml import etree
import time
import os
import random
from retrying import retry
import urllib3
import re

# 解决Python3 控制台输出InsecureRequestWarning的问题。也就是针对warn不提示
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 公共变量
session = requests.Session()
url_root = r"https://www.100sht.space/forum.php?mod=forumdisplay"
url_every = r"https://www.100sht.space/{}"
img_Path = r"C:\Users\Administrator\Desktop\pythonStydy\爬虫\data\sehuatang\img"
headers = {
    # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    # 'Accept-Encoding': 'gzip, deflate, br',
    # 'Accept-Language': 'zh-CN,zh;q=0.9',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Cookie': 'cPNj_2132_saltkey=ncyxfLqu; cPNj_2132_lastvisit=1561564948; cPNj_2132_atarget=1; UM_distinctid=16b94bcc60b15c-03e48b68817b36-3e38580a-13c680-16b94bcc60c72; cPNj_2132_visitedfid=98D41; CNZZDATA1273692513=136776695-1561567772-%7C1561649998; cPNj_2132_st_t=0%7C1561652508%7Cb5e23803812a1d557fd0ee5fe7d039c3; cPNj_2132_forum_lastvisit=D_41_1561574143D_98_1561652508; cPNj_2132_secqaa=492080.6005e5f74c3f840464; cPNj_2132_sid=Pk7m4T; cPNj_2132_st_p=0%7C1561653878%7C508e00bea387d2f5b2fbe52affa54733; cPNj_2132_viewid=tid_135147; cPNj_2132_lastact=1561653879%09home.php%09misc; cPNj_2132_sendmail=1',
    'Host': 'www.100sht.space',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36'
}

# 动态传入referer，反爬
def getHeaders(referer):
    headersForDownload = {
        'Referer': referer,
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36'
    }
    return headersForDownload

# 校正“创建文件夹使用了windows的非法字符串”的bug
def validateWindowsStr(str):
    rstr = r"[\/\\\:\*\?\"\<\>\|\!\！\？]"  # 识别'/ \ : * ? " < > ! |'
    new_str = re.sub(rstr, " ", str)  # 替换为空格
    return new_str

# 创建的文件夹不允许以.结尾。递归。
def dropErrorStr(str):
    if str.endswith('.'):
        str = str[:-1]
        return dropErrorStr(str)
    else:
        return str

# 获取网站响应一定要加上这个请求配置的注解，不然时常会报错。
@retry(stop_max_attempt_number=5, wait_fixed=2000)
def get_request(url, referer):
    response = requests.get(url, headers=getHeaders(referer), timeout=2, verify=False)
    return response.content

# 获取网站响应一定要加上这个请求配置的注解，不然时常会报错。
@retry(stop_max_attempt_number=5, wait_fixed=2000)
def session_get_request(url):
    response = session.get(url, headers=headers, timeout=2, verify=False)
    return response

# 一级主页解析
def parse_navigation(content):
    tree = etree.HTML(content)
    a_list = tree.xpath("//tbody[contains(@id,'normalthread')]//th//a[contains(@href,'html')]/@href")
    for href in a_list:
        href = url_every.format(href)
        print("开始处理页面：", href)
        deal_every_page(href)
        time.sleep(random.random() * 3)

# 二级详情页面解析
def deal_every_page(href):
    try:
        r = session_get_request(href)
        tree = etree.HTML(r.text)
        image_src_list = tree.xpath(
            "//ignore_js_op//div[contains(@class,'savephotop')]//img[contains(@file,'jpg')]/@file")
        title = tree.xpath("//span[@id='thread_subject']/text()")[0]
        # print("len(image_src_list):", len(image_src_list))
        if len(image_src_list) < 1:
            image_src_list = tree.xpath("//table//td[contains(@id,'postmessage')]//img[contains(@file,'http')]/@file")
        download(href, title, image_src_list)
    except:
        print("本页面处理失败:", href)

# 下载任务
def download(href, title, image_src_list):
    dirname = img_Path + '\\' + dropErrorStr(validateWindowsStr(str(title)))

    if not os.path.exists(dirname):
        print("创建文件夹：", dirname)
        os.mkdir(dirname)

    # 把本页面的网址存入该文件夹，txt文件
    if not os.path.exists((dirname + '\\url.txt')):
        with open((dirname + '\\url.txt'), 'w', encoding='utf8') as f:
            f.write(href)

    print("正在下载: %s系列图片 ......" % title)
    for image_src in image_src_list:
        filename = image_src.split('/')[-1]
        filepath = dirname + '\\' + filename
        if os.path.exists(filepath):
            break
        try:
            content = get_request(image_src, href)
            # response = requests.get(url=image_src, headers=getHeaders(href), timeout=2)
            with open(filepath, 'wb') as f:
                f.write(content)
        except:
            print("下载失败:", image_src)
            continue
        # urllib.request.urlretrieve(image_src, filepath)

    print("结束下载: %s系列图片 ......" % title)
    print()

# 主函数入口
def main():
    # 准备爬取第1页到第379页 （所有页）
    start_page = int(input("请输入起始页："))
    end_page = int(input("请输入结束页："))
    for pageNum in range(start_page, end_page + 1):
        data = {
            'fid': '98',
            'page': pageNum,
            't': random.randint(0, 99999999)
        }
        r = session.get(url=url_root, headers=headers, params=data)
        print('第 %s 页 开始执行...... ' % pageNum)
        parse_navigation(r.text)
        print('第 %s 页 执行结束...... ' % pageNum)
        print()
        time.sleep(random.random() * 5)


if __name__ == '__main__':
    main()
