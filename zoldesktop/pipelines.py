# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import scrapy
from scrapy.pipelines.images import ImagesPipeline


class ZoldesktopPipeline:
    def process_item(self, item, spider):
        return item

class MyImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        for url in item['image_urls']:
            name = item['name']
            yield scrapy.Request(url, meta={'name': name})

    def file_path(self, request, response=None, info=None):
        dir_name = request.meta['name'].split('（')[0]
        file_name = request.meta['name'].replace('/', '_')
        return '%s/%s.jpg' %(dir_name, file_name)