# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json

import minio
import pymongo
from scrapy import Request
from scrapy.exceptions import DropItem
from scrapy.pipelines.files import FilesPipeline
from scrapy.pipelines.images import ImagesPipeline
from indopacom_spider.spiders.pacom import PacomSpider


# 新闻、官网、军演类 pipeline
class IndopacomNewsSpiderPipeline(object):

    def __init__(self, mongo_url, mongo_db, mongo_table, mongo_port, mongo_user, mongo_pwd,
                 minio_url, minio_user, minio_pwd, minio_bucket):
        # MongoDB
        self.mongo_url = mongo_url
        self.mongo_db = mongo_db
        self.mongo_table = mongo_table
        self.mongo_port = mongo_port
        self.mongo_user = mongo_user
        self.mongo_pwd = mongo_pwd

        # MinIO
        self.minio_url = minio_url
        self.minio_user = minio_user
        self.minio_pwd = minio_pwd
        self.minio_bucket = minio_bucket

    @classmethod
    def from_crawler(cls, crawl):
        return cls(
            mongo_url=crawl.settings.get('MONGO_URL'),
            mongo_db=crawl.settings.get('MONGO_DB'),
            mongo_table=crawl.settings.get('MONGO_NEWS_TABLE'),
            mongo_port=crawl.settings.get('MONGO_PORT'),
            mongo_user=crawl.settings.get('MONGO_USER'),
            mongo_pwd=crawl.settings.get('MONGO_PWD'),

            minio_url=crawl.settings.get('MINIO_URL'),
            minio_user=crawl.settings.get('MINIO_USER'),
            minio_pwd=crawl.settings.get('MINIO_PWD'),
            minio_bucket=crawl.settings.get('MINIO_BUCKET'),
        )

    def open_spider(self, spider):
        """
            爬虫一旦开启，就会实现这个方法，连接到数据库
        """
        self.minio_client = minio.Minio(endpoint=self.minio_url, access_key=self.minio_user,
                                        secret_key=self.minio_pwd, secure=False)

        self.client = pymongo.MongoClient(self.mongo_url)
        self.db = self.client[self.mongo_db]
        # self.db.authenticate(self.mongo_user, self.mongo_pwd, mechanism='SCRAM-SHA-1')
        self.mongo_client = self.db[self.mongo_table]

    def process_item(self, item, spider):
        # if isinstance(spider, PacomSpider):
        item_data = dict(item)
        # 图片数据
        img_data = item_data['img_data']
        if img_data:
            for __img in img_data:
                print(__img["img_name"])
                minio_response = self.minio_client.get_object(self.minio_bucket, __img["img_name"])
                with open(f'indopacom_spider/resource/zip_file/{__img["img_name"]}', 'wb') as f:
                    f.write(minio_response.read())
        # 文本数据
        with open("indopacom_spider/resource/zip_file/data.txt", "a+", encoding="utf8") as f:
            f.write(json.dumps(item_data, ensure_ascii=False) + '\n')

        self.mongo_client.insert_one(item_data)
        # else:
        #     return item

    def close_spider(self, spider):
        """
        爬虫一旦关闭，就会实现这个方法，关闭数据库连接
        """
        # print(spider.crawler.stats.get_stats())
        # scrapy_crawl_stats = spider.crawler.stats.get_stats()
        self.client.close()


# 听证会类 pipeline
class IndopacomHearingSpiderPipeline(object):

    def __init__(self, mongo_url, mongo_db, mongo_table, mongo_port, mongo_user, mongo_pwd):
        self.mongo_url = mongo_url
        self.mongo_db = mongo_db
        self.mongo_table = mongo_table
        self.mongo_port = mongo_port
        self.mongo_user = mongo_user
        self.mongo_pwd = mongo_pwd

    @classmethod
    def from_crawler(cls, crawl):
        return cls(
            mongo_url=crawl.settings.get('MONGO_URL'),
            mongo_db=crawl.settings.get('MONGO_DB'),
            mongo_table=crawl.settings.get('MONGO_HEARINGS_TABLE'),
            mongo_port=crawl.settings.get('MONGO_PORT'),
            mongo_user=crawl.settings.get('MONGO_USER'),
            mongo_pwd=crawl.settings.get('MONGO_PWD')
        )

    def open_spider(self, spider):
        """
            爬虫一旦开启，就会实现这个方法，连接到数据库
        """
        self.client = pymongo.MongoClient(self.mongo_url)
        self.db = self.client[self.mongo_db]
        # self.db.authenticate(self.mongo_user, self.mongo_pwd, mechanism='SCRAM-SHA-1')
        self.mongo_client = self.db[self.mongo_table]

    def process_item(self, item, spider):
        # if isinstance(spider, PacomSpider):
        self.mongo_client.insert_one(dict(item))
        # else:
        #     return item

    def close_spider(self, spider):
        """
        爬虫一旦关闭，就会实现这个方法，关闭数据库连接
        """
        # print(spider.crawler.stats.get_stats())
        # scrapy_crawl_stats = spider.crawler.stats.get_stats()
        self.client.close()


# 图片 pipeline
class SaveImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        # 下载图片，如果传过来的是集合需要循环下载
        # meta里面的数据是从spider获取，然后通过meta传递给下面方法：file_path
        # yield Request(url=item['url'],meta={'name':item['title']})
        if item['img_data']:
            for img_item in item['img_data']:
                yield Request(url=img_item['img_url'], meta={'name': img_item['img_name']})

    def item_completed(self, results, item, info):
        # 是一个元组，第一个元素是布尔值表示是否成功
        # if not results[0][0]:
        #     raise DropItem('下载失败')
        return item

    # 重命名，若不重写这函数，图片名为哈希，就是一串乱七八糟的名字
    def file_path(self, request, response=None, info=None):
        # 接收上面meta传递过来的图片名称
        name = request.meta['name']
        # 提取url前面名称作为图片名
        # image_name = request.url.split('/')[-1]
        # 清洗Windows系统的文件夹非法字符，避免无法创建目录
        # folder_strip = re.sub(r'[？\\*|“<>:/]', '', str(name))
        # 分文件夹存储的关键：{0}对应着name；{1}对应着image_guid
        # filename = u'{0}/{1}'.format(folder_strip, image_name)
        # filename = u'{0}'.format(folder_strip)

        return name


# 文件 pipeline
class SaveFilesPipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        for file_item in item['file_url_list']:
            yield Request(url=file_item['file_url'], meta={'name': file_item['file_location_name']})

    def item_completed(self, results, item, info):
        return item

    def file_path(self, request, response=None, info=None):
        name = request.meta['name']
        return name
