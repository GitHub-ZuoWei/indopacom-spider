# -*- coding: utf-8 -*-
import time

import bson
import scrapy
from lxml import etree
from readability import Document

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


class PacomSpider(scrapy.Spider):
    name = 'pacom'
    start_urls = ['https://www.pacom.mil/Media/News/']

    # custom_settings = {
    #     'ITEM_PIPELINES': {'indopacom_spider.pipelines.SaveImagePipeline': 1,
    #                        'indopacom_spider.pipelines.IndopacomNewsSpiderPipeline': 300}
    # }

    # rules = (
    #     Rule(LinkExtractor(allow=r'https://www.pacom.mil/Media/News/?Page=\d+', ), callback='parse_sec', follow=True)
    # )

    def start_requests(self):
        # yield Request(url=self.start_urls, callback=self.parse, dont_filter=False,meta={'proxy': 'http://192.168.12.180:6666'})
        # 'https://www.pacom.mil/Media/News/?Page=11'

        yield Request(url=self.start_urls[0], callback=self.parse_item, dont_filter=True)

    # 解析列表页
    def parse_item(self, response):
        # 总页数
        page_sum = response.xpath('//*["@class=pagination"][last()]/li[last()]/a/span/text()').extract_first()
        self.logger.info(f'新闻总页数为:{page_sum}')
        self.logger.info(f'列表页URL:{response.url}')

        news_list = response.xpath('//*[@id="linkTitle"]/a/@href').extract()
        for item in news_list:
            yield Request(url=item, callback=self.parse_content, dont_filter=False)

        # 获取下一页链接
        next_url = response.xpath("//ul[contains(@class,'pagination')]"
                                  "/li[contains(@class,'active')]"
                                  "/following-sibling::li[1]/a/@href").extract_first()
        if next_url:
            yield Request(url=next_url, callback=self.parse_item, dont_filter=True)

    # 解析详情页
    def parse_content(self, response):
        self.logger.info(f'详情页URL:{response.url}')

        document = Document(response.text)
        html_content = document.summary(html_partial=True)
        content = etree.HTML(html_content).xpath('string(.)').strip()

        publish_time = response.xpath('//div[@class="category-date"]/text()').extract()[1]
        if publish_time:
            publish_time = format_date(publish_time.replace(' | ', ''))

        source = ''
        author = response.xpath('string(//*[@class="header"]/p)').extract_first().strip()
        if author:
            author_and_source = author.split('\n')
            if len(author_and_source) > 1:
                author = author_and_source[0].strip()
                source = author_and_source[1].strip()

        img_url = response.xpath('//img[@class="aimage img-responsive"]/@src').extract_first()
        img_describe = response.xpath('//div[@class="image-caption"]/text()').extract_first()

        img_data = []
        if img_url:
            img_data = [{
                'img_url': img_url,
                'img_describe': img_describe,
                'img_name': f'news/img_{time.strftime("%Y_%m_%d_")}{bson.ObjectId()}.png',
            }]

        # yield Request(url='http://www.baidu.com', callback=self.parse_img, dont_filter=True, meta={'item': item})
        yield IndopacomNewsSpiderItem(title=document.short_title(),
                                      publish_time=publish_time,
                                      author=format_author(author),
                                      content=content,
                                      content_html=html_content,
                                      source=source,
                                      keywords=[],
                                      categories=[],
                                      img_data=img_data,
                                      video_data=[],
                                      url=response.url,
                                      site_name=self.name,
                                      insert_time=time.strftime('%Y-%m-%d %H:%M:%S'))
