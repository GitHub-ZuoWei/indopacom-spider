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


class C4isrnetSpider(scrapy.Spider):
    name = 'c4isrnet'
    start_urls = ['http://www.c4isrnet.com/']

    def start_requests(self):
        self.logger.info(f'新闻总页数为:{1000 / 20}')
        for page_num in range(0, 1000, 20):
            self.logger.info(f'列表页URL:{(page_num / 20) + 1}')
            param = f'{{"from":{page_num},"section":"/home","size":20}}'
            page_url = f'https://www.c4isrnet.com/pf/api/v3/content/fetch/mco-story-query?' \
                       f'filter={{_id,content_elements{{_id,website_url,count,next,size,type}}' \
                       f'&d=40&_website=c4isrnet&query={param}'
            yield Request(url=page_url, callback=self.parse_item, dont_filter=True)

    def parse_item(self, response):
        response_json = response.json().get('content_elements')
        for item in response_json:
            yield response.follow(url=item['website_url'], callback=self.parse_content, dont_filter=True)

    def parse_content(self, response):
        self.logger.info(f'详情页URL:{response.url}')
        extractor = GeneralNewsExtractor()
        extract_result = extractor.extract(html=response.text,
                                           with_body_html=True,
                                           noise_node_list=['//div[contains(@class,"List__Wrapper")]',
                                                            '//div[contains(@class,"default__Wrapper")]',
                                                            '//div[contains(@class,"InterstitialLink")]'],
                                           title_xpath='//h1[contains(@class,"Heading__H1")]/text()',
                                           author_xpath='//*[contains(@itemprop,"author")]/text()',
                                           publish_time_xpath='string(//div[@class="c-articleHeader__date"])',
                                           # body_xpath='//*[@class="main"]'
                                           )
        # 新闻作者
        news_author = extract_result['author'].strip()
        # 新闻发布时间
        news_publish_time = extract_result['publish_time'].strip()
        # 新闻标题
        news_title_gne = extract_result['title']
        # 新闻内容
        news_content_gne = extract_result['content']
        # 新闻内容 HTML
        news_content_html_gne = extract_result['body_html']
        if not news_author:
            news_author = response.xpath('//span[contains(@class,"Byline__Author")]/text()').extract_first()
        else:
            author_split = news_author.replace('  ', ' ').split(' ')
            if author_split:
                error_author = author_split[-1] + author_split[0]
                news_author = news_author.replace(error_author, '').replace('  ', ' ')

        if news_publish_time:
            news_publish_time = format_date(news_publish_time.strip())

        img_url = response.xpath('//div[contains(@class,"ArticleHeader__LeadArtWrapper")]/link/@href').extract_first()
        img_describe = response.xpath('string(//figcaption[@class="a-caption"])').extract_first()

        img_data = []
        if img_url:
            img_name = f'news/img_{time.strftime("%Y_%m_%d_")}{bson.ObjectId()}.png'
            img_data = [{
                'img_url': img_url,
                'img_describe': img_describe,
                'img_name': img_name,
            }]
            news_content_html_gne = news_content_html_gne.replace(img_url, f'{img_name}')

        yield IndopacomNewsSpiderItem(title=news_title_gne,
                                      publish_time=news_publish_time,
                                      author=format_author(news_author),
                                      content=news_content_gne,
                                      content_html=news_content_html_gne,
                                      source='',
                                      keywords=[],
                                      categories=[],
                                      img_data=img_data,
                                      video_data=[],
                                      url=response.url,
                                      site_name=self.name,
                                      insert_time=time.strftime('%Y-%m-%d %H:%M:%S'))
