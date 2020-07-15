# -*- coding: utf-8 -*-
import logging
import sys
from concurrent.futures.thread import ThreadPoolExecutor
from queue import Queue

import scrapy
from PyQt5.QtWidgets import QApplication, QWidget

from zoldesktop.items import ZoldesktopItem



class Example(QWidget):
    def __init__(self):
        super().__init__()

    def initUI(self):
        self.desktop = QApplication.desktop()
        # 获取显示器分辨率大小
        self.screenRect = self.desktop.screenGeometry()
        self.height = self.screenRect.height()
        self.width = self.screenRect.width()
        return (str(self.width) + 'x' + str(self.height))


class ZolpSpider(scrapy.Spider):
    name = 'zolp'
    allowed_domains = ['desk.zol.com.cn']
    start_urls = ['http://desk.zol.com.cn/pc/']
    pages = 0
    jishu = 0
    choice_class = 1
    # 创建队列
    list_que = Queue()
    image_que = Queue()
    # 创建线程池
    pool = ThreadPoolExecutor(10)

    # 创建应用程序和对象
    app = QApplication(sys.argv)
    display = Example()
    # 获取分辨率
    fenbianlv = display.initUI()

    def parse(self, response):
        # 解析首页, 获取分类/分辨率地址
        classify_name = response.xpath(
            '//dd[@class="brand-sel-box clearfix"]/a[not(@class="all sel")]/text()').extract()[:34]
        classfiy_href = response.xpath('//dd[@class="brand-sel-box clearfix"]/a/@href').extract()[:34]
        classify_dict = { }
        for name, href in zip(classify_name, classfiy_href):
            classify_dict[name.split('(')[0]] = href

        print('{:<8s}'.format("""
                    风景\t\t\t动漫\t\t\t美女\t\t\t创意\t\t\t卡通        
                    汽车\t\t\t游戏\t\t\t可爱\t\t\t明星\t\t\t建筑       
                    植物\t\t\t动物\t\t\t静物\t\t\t影视\t\t\t车模   
                    体育\t\t\t模特\t\t\t手抄报\t\t\t美食\t\t\t星座  
                    节日\t\t\t品牌\t\t\t背景\t\t\t其他  
                    """))
        print('-' * 100)
        print('{:<10s}'.format("""
                    4096x2160\t\t2560x1440\t\t2880x1800\t\t2560x1600
                    1920x1200\t\t1920x1080\t\t1680x1050\t\t1600x900
                    1440x900\t\t1280x1024
            """))
        while True:
            print('说明: 若选择分类则默认以您当前屏幕分辨率下载, 若选择分辨率则默认以选择的分辨率下载.')
            classify = input('请输入(分类/分辨率)列表中的选项:')
            print('您的选择是: %s .' % classify)
            key_list = []
            for key in classify_dict.keys():
                key_list.append(key)
            if classify in key_list:
                print('http://desk.zol.com.cn' + classify_dict[classify])
                ratio_choice = 1
                if key_list.index(classify) >= 23:
                    self.choice_class = 0
                    ratio_choice = classify
                yield scrapy.Request('http://desk.zol.com.cn' + classify_dict[classify], callback=self.parse_list,
                                     meta={ 'ratio': ratio_choice })
                break
            else:
                print('输入错误, 请重新输入...')

    def parse_list(self, response):
        print('正在解析 组图 列表: ', response.url)
        group_href = response.xpath('//li[@class="photo-list-padding"]/a[@class="pic"]/@href').extract()
        next_href = response.xpath('//div/a[@id="pageNext"]/@href').extract_first()
        pict_sum = response.xpath('//dd/span[2]/font/text()').extract_first()
        ratio = response.meta['ratio']
        if response.url.find('.html') == -1:
            page = int(pict_sum) // 21
            while True:
                try:
                    num = int(input("请输入需要下载的页数 (当前组图共有%d页.): " % (page)))
                    print('您的输入是: %d' % num)
                except:
                    print('页数错误, 请重新输入...')
                    continue
                if 0 < num <= page:
                    self.pages = num
                    break
                else:
                    print('页数错误, 请重新输入...')
        for each in group_href:
            # yield scrapy.Request('http://desk.zol.com.cn' + each, callback=self.parse_image, meta={'ratio': ratio})
            self.pool.submit(self.parse_image, 'http://desk.zol.com.cn' + each)
        if self.pages > 1:
            self.pages -= 1
            yield scrapy.Request('http://desk.zol.com.cn' + next_href, callback=self.parse_list, meta={'ratio': ratio})

    def parse_image(self, response):
        ratio_id = response.xpath('//dd[@id="tagfbl"]/a/@id').extract()
        ratio_href = response.xpath('//dd[@id="tagfbl"]/a[@id]/@href').extract()
        names = response.xpath('//h3')
        name = names.xpath('string(.)').extract()[0].strip().replace('\r\n\t\t', '')
        print('正在解析 %s 详情... ' % name)
        ratio = { }
        for ids, href in zip(ratio_id, ratio_href):
            ratio[ids] = href
        if self.choice_class == 0:
            choice_ratio = response.meta['ratio']
            if choice_ratio in ratio.keys():
                yield scrapy.Request('http://desk.zol.com.cn' + ratio[choice_ratio], callback=self.parse_down, meta={ 'name': name })
            else:
                yield scrapy.Request('http://desk.zol.com.cn' + response.xpath('//div/img[@id="bigImg"]/@src').extract_first(),
                                     callback=self.parse_down, meta={ 'name': name })
        else:
            default = self.fenbianlv
            if default in ratio.keys():
                yield scrapy.Request('http://desk.zol.com.cn' + ratio[default], callback=self.parse_down, meta={ 'name': name })
            else:
                yield scrapy.Request('http://desk.zol.com.cn' + response.xpath('//div/img[@id="bigImg"]/@src').extract_first(),
                                     callback=self.parse_down, meta={ 'name': name })

        next_href = response.xpath('//ul[@id="showImg"]/li/a/@href').extract()
        for each_next in next_href:
            # yield scrapy.Request('http://desk.zol.com.cn' + each_next, callback=self.parse_image)
            self.pool.submit(self.parse_image, 'http://desk.zol.com.cn' + each_next)

    def parse_down(self, response):
        self.jishu += 1
        image_url = response.xpath('/html/body/img[1]/@src').extract_first()
        item = ZoldesktopItem()
        name = response.meta['name']
        print('正在下载并保存 %s ...' % name)
        print('总计 已下载  %s  张壁纸. ' % self.jishu)
        item['name'] = name
        item['image_urls'] = [image_url]
        yield item
