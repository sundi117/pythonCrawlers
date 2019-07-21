#!/usr/bin/env python3
# _*_ coding:utf-8 _*_
#
# @Desc    : 韩国限制级电影爬虫  http://www.22hyk.com
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

# 解决Python3 控制台输出InsecureRequestWarning的问题。也就是针对warn信息不提示
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 公共变量
session = requests.Session()
url_root = r"http://www.22hyk.com/forum.php?mod=forumdisplay"
url_every = r"http://www.22hyk.com/{}"
torrent_Path = r"D:\data\爬虫\爬出\torrent"   # 本地目标文件夹（请修改）
referer = 'http://www.22hyk.com/forum.php?mod=forumdisplay&fid=56&page=25'
headers = {
    # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    # 'Accept-Encoding': 'gzip, deflate, br',
    # 'Accept-Language': 'zh-CN,zh;q=0.9',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Referer': referer,
    'Cookie': 'svQ1_2132_saltkey=I4PB222e; svQ1_2132_lastvisit=1563591210; svQ1_2132_visitedfid=56; svQ1_2132_st_t=0%7C1563628116%7C3ad065f131ed0ad2238c34a94f8c8227; svQ1_2132_forum_lastvisit=D_56_1563628116; svQ1_2132_sid=wkBr3k; svQ1_2132_ulastactivity=b4b5PY5%2FtDAw9yACAyyNjlk%2BIZz8RWKvCxfB8C5a0TBXgqYanV1P; svQ1_2132_auth=6b66E5dcHk%2FHyggxSC6EFyfxJv%2FNUDkI8dLDfRr2mul%2F1L5miAc7SjVMQtAziHdCBrAWNlgtJutzv1mhfjh9RPWm%2Bng; svQ1_2132_st_p=242520%7C1563638719%7Cd86047781b66812f720bd42e4a6d412d; svQ1_2132_viewid=tid_12374; svQ1_2132_lastact=1563638721%09home.php%09spacecp',
    'Host': 'www.22hyk.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36'
}
# 经检查:若直接使用公共headers下载个别图片时候会报错，发现是host引起的，现在只保留User-Agent,Cookie（cookie为我个人账号登录后的cookie）
headersForDownloadImage = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
    'Cookie': 'svQ1_2132_saltkey=I4PB222e; svQ1_2132_lastvisit=1563591210; svQ1_2132_visitedfid=56; svQ1_2132_st_t=0%7C1563628116%7C3ad065f131ed0ad2238c34a94f8c8227; svQ1_2132_forum_lastvisit=D_56_1563628116; svQ1_2132_sid=wkBr3k; svQ1_2132_ulastactivity=b4b5PY5%2FtDAw9yACAyyNjlk%2BIZz8RWKvCxfB8C5a0TBXgqYanV1P; svQ1_2132_auth=6b66E5dcHk%2FHyggxSC6EFyfxJv%2FNUDkI8dLDfRr2mul%2F1L5miAc7SjVMQtAziHdCBrAWNlgtJutzv1mhfjh9RPWm%2Bng; svQ1_2132_st_p=242520%7C1563638719%7Cd86047781b66812f720bd42e4a6d412d; svQ1_2132_viewid=tid_12374; svQ1_2132_lastact=1563638721%09home.php%09spacecp',
}
data = {}


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

# 某些图片url没有网站头，需要补上
def validataURL(url):
    if url.lower().find('http') == -1:
        url = url_every.format(url)
    return url

# 获取网站响应一定要加上这个请求配置的注解，不然时常会报错。
@retry(stop_max_attempt_number=5, wait_fixed=2000)
def get_request(url, headers=headers, referer=referer, params=data):
    if params:
        response = requests.get(url, headers=headers, params=params, timeout=5, verify=False)
    else:
        response = requests.get(url, headers=headers, timeout=5, verify=False)
    return response

# 一级主页解析
def parse_navigation(content):
    tree = etree.HTML(content)
    a_list = tree.xpath(
        "//tbody[contains(@id,'normalthread')]//div[contains(@class,'dzlist')]//span[@class='dzlist_common']/a[contains(@href,'forum')]/@href")

    for href in a_list:
        href = url_every.format(href)
        print("开始处理页面：", href)
        deal_every_page(href)
        time.sleep(random.random() * 3)

# 二级详情页面解析
def deal_every_page(href):
    try:
        r = get_request(href)
        tree = etree.HTML(r.text)
        title = tree.xpath("//span[@id='thread_subject']/text()")[0]

        imgs_src_list = tree.xpath("//ignore_js_op//img[contains(@file,'jpg')]/@file")
        if len(imgs_src_list) < 1:
            imgs_src_list = tree.xpath("//ignore_js_op//img[contains(@src,'jpg')]/@src")
        if len(imgs_src_list) < 1:
            imgs_src_list = tree.xpath("//td[contains(@id,'postmessage')]//img[contains(@file,'jpg')]/@file")
        if len(imgs_src_list) < 1:
            imgs_src_list = tree.xpath("//td[contains(@id,'postmessage')]//img[contains(@src,'jpg')]/@src")

        torrent_title = tree.xpath("//ignore_js_op//a[contains(text(),'torrent')]//text()")[0]
        torrent_url = url_every.format(tree.xpath("//ignore_js_op//a[contains(text(),'torrent')]/@href")[0])
        # print("len(image_src_list):", len(image_src_list))
        download(href, title, imgs_src_list, torrent_title, torrent_url)
    except:
        print("本页面处理失败:", href)

# 下载任务
def download(href, title, imgs_src_list, torrent_title, torrent_url):
    # torrent_Path   D:\data\爬虫\爬出\torrent
    dirname = torrent_Path + '\\' + dropErrorStr(validateWindowsStr(str(title)))

    if not os.path.exists(dirname):
        print("创建文件夹：", dirname)
        os.mkdir(dirname)

    # 把本页面的网址存入该文件夹，txt文件
    if not os.path.exists((dirname + '\\url.txt')):
        with open((dirname + '\\url.txt'), 'w', encoding='utf8') as f:
            f.write(href)

    # 下载本页面的详情图片
    print("正在下载: %s 图片 ......" % title)
    for image_src in imgs_src_list:
        image_src = validataURL(image_src)
        filename = image_src.split('/')[-1]
        filepath = dirname + '\\' + filename
        if os.path.exists(filepath):
            continue
        try:
            content = get_request(image_src, headers=headersForDownloadImage).content
            with open(filepath, 'wb') as f:
                f.write(content)
        except:
            print("下载失败:", image_src)
            continue
    print("结束下载: %s 图片 ......" % title)

    # 下载种子
    print("正在下载: %s 种子 ......" % torrent_title)
    torrent_file_path = dirname + '\\' + torrent_title
    if not os.path.exists(torrent_file_path):
        try:
            content = get_request(validataURL(torrent_url)).content
            with open(torrent_file_path, 'wb') as f:
                f.write(content)
        except:
            print("下载失败:", torrent_file_path)
    print("结束下载: %s 种子 ......" % torrent_title)
    print()


# 主函数入口
def main():
    # 准备爬取第1页到第25页 （所有页）
    start_page = int(input("请输入起始页："))
    end_page = int(input("请输入结束页："))
    for pageNum in range(start_page, end_page + 1):
        data = {
            'fid': '56',
            'page': pageNum,
        }
        r = get_request(url=url_root, headers=headers, params=data)
        print('第 %s 页 开始执行...... ' % pageNum)
        parse_navigation(r.text)
        print('第 %s 页 执行结束...... ' % pageNum)
        print()
        time.sleep(random.random() * 5)


if __name__ == '__main__':
    main()
