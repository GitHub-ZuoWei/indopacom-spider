import time

import bson
import scrapy

from lxml import etree
from lxml.etree import ElementTree
from readability import Document
from gne import GeneralNewsExtractor

from scrapy import Request, signals

from indopacom_spider.items import IndopacomNewsSpiderItem

from indopacom_spider.utils.format_author_util import format_author
from indopacom_spider.utils.format_date_util import format_date

"""
      ┏┛ ┻━━━━━┛ ┻┓
      ┃　　　　　　 ┃
      ┃　　　━　　　┃
      ┃　┳┛　  ┗┳　┃
      ┃　　　　　　 ┃
      ┃　　　┻　　　┃
      ┃　　　　　　 ┃
      ┗━┓　　　┏━━━┛
        ┃　　　┃   神兽保佑
        ┃　　　┃   代码无BUG！
        ┃　　　┗━━━━━━━━━┓
        ┃　　　　　　　    ┣┓
        ┃　　　　         ┏┛
        ┗━┓ ┓ ┏━━━┳ ┓ ┏━┛
          ┃ ┫ ┫   ┃ ┫ ┫
          ┗━┻━┛   ┗━┻━┛
"""


# https://www.military.com/topics/headlines
class MilitarySpider(scrapy.Spider):
    name = 'military'
    start_urls = ['http://www.military.com/']
    page_num = 10
    total_num = 1000

    def start_requests(self):
        self.logger.info(f'新闻总页数为:{self.total_num / self.page_num}')
        for page_id in range(0, self.total_num, self.page_num):
            self.logger.info(f'列表页URL:{(int(page_id / self.page_num)) + 1}')
            page_url = f'https://www.military.com/topics/headlines?page={int(page_id / self.page_num)}'
            yield Request(url=page_url, callback=self.parse_item, dont_filter=True)

    def parse_item(self, response):
        news_list = response.xpath('//div[@class="list-view"]//div[@class="thumbnail--large"]/a/@href').extract()
        for item in news_list:
            yield response.follow(url=item, callback=self.parse_content, dont_filter=True)

    def parse_content(self, response):
        self.logger.info(f'详情页URL:{response.url}')
        extractor = GeneralNewsExtractor()
        extract_result = extractor.extract(html=response.text,
                                           with_body_html=True,
                                           # noise_node_list=['//div[contains(@class,"share-widget")]',
                                           #                  '//div[contains(@class,"full-in-small")]',
                                           #                  '//div[contains(@class,"authors")]',
                                           #                  '//div[contains(@class,"slideshow")]',
                                           #                  '//div[contains(@class,"inline-image align-center")]'],
                                           # title_xpath='//h1[contains(@class,"Heading__H1")]/text()',
                                           author_xpath='string(//div[@class="source"]/span[last()])',
                                           # publish_time_xpath='string(//span[@itemprop="datePublished"])',
                                           # body_xpath='//div[@id="article-text"]'
                                           )
        # 新闻作者
        news_author = extract_result['author'].replace('By', '').strip()
        # 新闻发布时间
        news_publish_time = extract_result['publish_time'].strip()
        # 新闻标题
        news_title_gne = extract_result['title']
        # 新闻内容
        news_content_gne = extract_result['content']
        # 新闻内容 HTML
        news_content_html_gne = extract_result['body_html']

        # 关键词
        keywords = response.xpath('//div[@class="field field--keywords field--label-inline"]/a/text()').extract()

        # 图片
        img_url = response.xpath('//div[@class="field field--image field--label-hidden"]/picture/img/@src').extract_first()
        img_describe = response.xpath('//div[@class="field field--image field--label-hidden"]/picture/img/@title').extract_first()
        img_data = []
        if img_url:
            img_name = f'news/img_{time.strftime("%Y_%m_%d_")}{bson.ObjectId()}.png'
            img_data = [{
                'img_url': response.urljoin(img_url),
                'img_describe': img_describe,
                'img_name': img_name,
            }]

        yield IndopacomNewsSpiderItem(title=news_title_gne,
                                      publish_time=format_date(news_publish_time),
                                      author=format_author(news_author),
                                      content=news_content_gne,
                                      content_html=news_content_html_gne,
                                      source='',
                                      keywords=keywords,
                                      categories=[],
                                      img_data=img_data,
                                      video_data=[],
                                      url=response.url,
                                      site_name=self.name,
                                      insert_time=time.strftime('%Y-%m-%d %H:%M:%S'))