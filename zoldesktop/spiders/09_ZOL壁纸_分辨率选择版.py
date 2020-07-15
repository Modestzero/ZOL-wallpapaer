import os
import re
from queue import Queue
from random import randint
from threading import Thread
from time import sleep
import requests
from lxml import etree


def select_ratio(url, choice):
    response = requests.get(url, headers=headers)
    e = etree.HTML(response.text)
    ratios_list = { }
    ratios_list['1'] = 'http://desk.zol.com.cn/pc/'
    for i, ratios in zip(range(2, 12), e.xpath('//dl[@class="filter-item clearfix"]/dd/a/@href')):
        ratios_list[str(i)] = 'http://desk.zol.com.cn{}'.format(ratios)
    print(ratios_list[choice])
    sum_page = ''.join(e.xpath('//span/font/text()'))
    return ratios_list[choice], sum_page

def download(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
    }
    response = requests.get(url, headers=headers)
    e = etree.HTML(response.text)
    return e

class Crawl_list(Thread):
    def __init__(self, url, page, url_list_queue):
        super().__init__()
        self.url = url
        self.page = page
        self.url_list_queue = url_list_queue

    def run(self):
        for i in range(0, self.page):
            print('正在解析第{}页壁纸列表信息...'.format(i+1))
            e = download(self.url)
            url_list = e.xpath('//li[@class="photo-list-padding"]/a/@href')
            url_next = e.xpath('//div[@class="page"]/a[@class="next"]/@href')
            for each in url_list:
                self.url_list_queue.put('http://desk.zol.com.cn{}'.format(each))
            self.url = 'http://desk.zol.com.cn{}'.format(url_next[0])
            sleep(t)

class Parse_image(Thread):
    def __init__(self, choice_ratio, url_list_queue, image_url_queue):
        super().__init__()
        self.choice_ratio = choice_ratio
        self.url_list_queue = url_list_queue
        self.image_url_queue = image_url_queue

    def run(self):
        print('正在解析图片地址...')
        while self.url_list_queue.empty() == False:
            url = self.url_list_queue.get()
            e = download(url)
            ratio_href = e.xpath('//dd/a/@id')
            image_name = e.xpath('//div/h3/a/text()')[0]
            next_href = e.xpath('//div/a[@id="pageNext"]/@href')[0]
            serial_number = e.xpath('//span/span/text()')
            if next_href != 'javascript:;':
                sleep(t)
                if self.choice_ratio in ratio_href:
                    href = ''.join(e.xpath('//dd/a[@id="{}"]/@href'.format(self.choice_ratio)))
                    image_url = image_name + '_' + ''.join(serial_number) + '-' + 'http://desk.zol.com.cn{}'.format(href)
                    self.image_url_queue.put(image_url)
                    next_p = 'http://desk.zol.com.cn{}'.format(next_href)
                    self.url_list_queue.put(next_p)
                else:
                    next_p = 'http://desk.zol.com.cn{}'.format(next_href)
                    self.url_list_queue.put(next_p)
            else:
                if self.choice_ratio in ratio_href:
                    href = ''.join(e.xpath('//dd/a[@id="{}"]/@href'.format(self.choice_ratio)))
                    image_url = image_name + '_' + ''.join(serial_number) + '-' + 'http://desk.zol.com.cn{}'.format(href)
                    self.image_url_queue.put(image_url)


class Down_Image(Thread):
    def __init__(self, image_url_queue):
        super().__init__()
        self.image_url_queue = image_url_queue

    def run(self):
        print('正在下载保存...')
        dir_h = os.getcwd() + '/download'
        try:
            os.mkdir(dir_h)
        except:
            pass
        while self.image_url_queue.empty() == False:
            name, url = self.image_url_queue.get().split('-')
            response = requests.get(url, headers=headers)
            src = re.findall(r'src="(https://.+)"', response.text)[0]
            if src[:6] != 'https:':
                pic_src = 'https://desk-fd.zol-img.com.cn' + src
            else:
                pic_src = src
            pic_info = requests.get(pic_src, headers=headers)
            dir_name = name.split('_')[0]
            new_dir = dir_h + '/{}'.format(dir_name)
            try:
                os.mkdir(new_dir)
            except:
                pass
            sleep(t)
            with open(new_dir +'/{}.jpg'.format(name), 'wb') as f:
                f.write(pic_info.content)
                f.flush()


if __name__ == '__main__':

    url_list_queue = Queue()
    url_next_queue = Queue()
    image_url_queue = Queue()

    start_url = 'http://desk.zol.com.cn/pc/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
    }
    # 随机睡眠时间
    t = randint(0, 2)

    print("""
                1. \t全部
                2. \t4096x2160(4k)
                3. \t2560x1440(2k)
                4. \t2880x1800(Retina屏)
                5. \t2560x1600(27-30英寸)
                6. \t1920x1200
                7. \t1920x1080(15-23英寸)
                8. \t1680x1050(22英寸)
                9. \t1600x900(20英寸)
                10.\t1440x900(15-19英寸)
                11.\t1280x1024(17-19英寸)
        """)
    choice_dict = {
        '1': '全部',
        '2': '4096x2160',
        '3': '2560x1440',
        '4': '2880x1800',
        '5': '2560x1600',
        '6': '1920x1200',
        '7': '1920x1080',
        '8': '1680x1050',
        '9': '1600x900',
        '10': '1440x900',
        '11': '1280x1024',

    }
    while True:
        choice = input('请输入需要的分辨率(默认: 7): ')

        if choice != '':
            if int(choice) in range(1, 12):
                choice_ratio = choice_dict[choice]
                break
            else:
                print('参数有误, 请重新输入...')
        else:
            choice = str(7)
            choice_ratio = choice_dict[choice]
            break

    url, sum_page = select_ratio(start_url, choice)
    while True:
        pages = input('每页有21组图片, 请输入需要下载的页数(默认: 1页): ')
        if pages != '':
            if int(pages) in range(1, int(sum_page)):
                page = int(pages)
                break
            else:
                print('页数错误, 请重新输入.')
        else:
            page = 1
            break

    image_list = Crawl_list(url, page, url_list_queue)
    image_list.start()
    image_list.join()

    parse_image = []
    for i in range(50):
        parses = Parse_image(choice_ratio, url_list_queue, image_url_queue)
        parse_image.append(parses)
        parses.start()
    for each in parse_image:
        each.join()

    down_image = []
    for i in range(30):
        save = Down_Image(image_url_queue)
        down_image.append(save)
        save.start()
    for each in down_image:
        each.join()
