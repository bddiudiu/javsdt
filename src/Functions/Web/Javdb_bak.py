# -*- coding:utf-8 -*-
import re, requests, cloudscraper
from Class.MyEnum import ScrapeStatusEnum
from traceback import format_exc
from Functions.Utils.XML import replace_xml_win
from Class.MyError import SpecifiedUrlError


# 搜索javbus，或请求javbus上jav所在网页，返回html
def get_db_html(url, proxy):
    scraper = cloudscraper.create_scraper()
    for retry in range(10):
        try:
            if proxy:
                rqs = scraper.get(url, proxies=proxy, timeout=(6, 7))
            else:
                rqs = scraper.get(url, timeout=(6, 7))
        except requests.exceptions.ProxyError:
            print(format_exc())
            print('    >通过局部代理失败，重新尝试...')
            continue
        except:
            print(format_exc())
            print('    >打开网页失败，重新尝试...')
            continue
        rqs.encoding = 'utf-8'
        rqs_content = rqs.text
        if rqs_content:
            return rqs_content
        else:
            print('    >打开网页失败，空返回...重新尝试...')
            continue
    input(f'>>请检查你的网络环境是否可以打开: {url}')


# 去javdb搜寻系列
# 返回: 系列名称，图片链接，状态码
def scrape_from_db(jav_file, jav_model, url_db, proxy_db):
    status = ScrapeStatusEnum.success
    # 用户指定了网址，则直接得到jav所在网址
    if '不支持指定搜索' in jav_file.Name:
        url_appointg = re.search(r'javadb(.+?)\.', jav_file.Name)
        if url_appointg:
            url_jav_db = f'{url_db}/{url_appointg.group(1)}'
            html_jav_bus = get_db_html(url_jav_db, proxy_db)
            titleg = re.search(r'<title>([A-Z].+?) - JAVLibrary</title>', html_jav_bus)  # 匹配处理“标题”
            if not titleg:
                raise SpecifiedUrlError(f'你指定的javdb网址找不到jav: {html_jav_bus}，')
        else:
            # 指定的网址有错误
            raise SpecifiedUrlError(f'你指定的javdb网址有错误: ')
    # 用户没有指定网址，则去搜索
    else:
        url_search = f'{url_db}/search?q={jav_file.Car}&f=all'
        print(f'    >搜索javdb: {url_search}')
        # 得到javdb搜索网页html
        html_search_db = get_db_html(url_search, proxy_db)
        list_search_results = re.findall(r'href="/v/(.+?)" class="box" title=".+?"[\s\S]*?uid">(.+?)</div>',html_search_db, re.DOTALL)
        if len(list_search_results) == 1:
            url_jav = f'{url_db}/v/{list_search_results[0][0].upper()}'
        # 第二种情况: 搜索结果可能是两个以上，所以这种匹配找不到标题，None！
        else:  # 找“可能是多个结果的网页”上的所有“box”
            # 从这些搜索结果中，找到最正确的一个
            if list_search_results:
                for i in list_search_results:
                    car_info = i[1].upper()
                    if jav_file.Car == car_info:
                        url_jav = f'{url_db}/v/{i[0]}?locale=zh'
            # 第三种情况: 搜索不到这部影片，搜索结果页面什么都没有
            else:
                return ScrapeStatusEnum.library_not_found, []
        # 打开这个jav在library上的网页
        print(f'    >获取信息: {url_jav}')
        html_jav_db = get_db_html(url_jav, proxy_db)
        # 标题
        if not jav_model.Title:
            jav_model.Title = re.findall(r'<h2 class="title is-4">.+?strong>(.+?)</strong>.+?</h2>', html_jav_db, re.DOTALL)[0].replace(jav_file.Car, "")
        if not jav_model.Car:
            # 车牌号
            jav_model.Car = jav_file.Car
        # 有大部分信息的html_jav_db
        html_jav_db = re.search(r'<div class="video-meta-panel">([\s\S]*?)want_to_watch" data-remote="true"', html_jav_db, re.DOTALL).group(1)
        # href="/cn/?v=javmeza25m"
        jav_model.Javdb = re.search(r'/v/(.+?)?locale=zh', url_jav).group(1)
        # DVD封面cover
        coverg = re.search(r'<img src="(.+?)"', html_jav_db)
        if coverg:
            cover_db = coverg.group(1)
            if not cover_db.startswith('http'):
                cover_db = f'http:{cover_db}'
            jav_model.CoverDb = cover_db
            jav_model.CarOrigin = jav_file.Car
        # 发行日期
        if jav_model.Release == '1970-01-01':
            premieredg = re.search(r'<span class="value">(\d\d\d\d-\d\d-\d\d)', html_jav_db)
            jav_model.Release = premieredg.group(1) if premieredg else '1970-01-01'
        # 片长 <td><span class="text">150</span> 分钟</td>
        if jav_model.Runtime == 0:
            runtimeg = re.search(r'value">(\d+) 分鐘<', html_jav_db)
            jav_model.Runtime = runtimeg.group(1) if runtimeg else 0
        # 导演
        if not jav_model.Director:
            directorg = re.search(r'directors/.+?">(.+?)<', html_jav_db)
            jav_model.Director = replace_xml_win(directorg.group(1)) if directorg else ''
        # 制作商
        if not jav_model.Studio:
            studiog = re.search(r'makers/.+?">(.+?)<', html_jav_db)
            jav_model.Studio = replace_xml_win(studiog.group(1)) if studiog else ''
        # 发行商
        if not jav_model.Publisher:
            publisherg = re.search(r'publishers/.+?">(.+?)<', html_jav_db)
            jav_model.Publisher = publisherg.group(1) if publisherg else ''
        # 系列
        if not jav_model.Series:
            serieserg = re.search(r'series/.+?">(.+?)<', html_jav_db)
            jav_model.Series = serieserg.group(1) if serieserg else ''
        # 演员们
        if not jav_model.Actors:
            jav_model.Actors = re.findall(r'actors/.+?">(.+?)</a><strong class="symbol female">', html_jav_db)
        # 评分
        if jav_model.Score == 0:
            scoreg = re.search(r'</span>&ngsp;(\d\.*\d*\d)分', html_jav_db)
            if scoreg:
                jav_model.Score = int(float(scoreg.group(1)) * 10)
        # 特点风格
        genres_db = re.findall(r'tags.+?">(.+?)</a>', html_jav_db)
    return status, genres_db
