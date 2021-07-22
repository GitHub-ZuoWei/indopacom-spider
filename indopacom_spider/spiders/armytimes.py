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


# https://www.armytimes.com/news/
class ArmytimesSpider(scrapy.Spider):
    name = 'armytimes'
    start_urls = ['http://www.armytimes.com/']
    # 每页数量
    page_num = 10
    # 新闻总数量
    total_num = 100

    def start_requests(self):
        self.logger.info(f'新闻总页数为:{self.total_num / self.page_num}')
        for page_id in range(0, self.total_num, self.page_num):
            self.logger.info(f'列表页URL:{int(page_id / self.page_num) + 1}')
            param = f'{{"_jg": "content-feed","Feed-Parameter": "/news","Feed-Limit": "10","Feed-Offset": {page_id}}}customFields={{"hideArtwork":"false","artworkPosition":"right","hideSubhead":"false","offset":"0","commentsCountCivil":"false","enabledDate":"true","showAuthor":"true","display3":"false","display2":"false","showDate":"true","commentsCountDisqus":"false","enabledAuthor":"true","numItems":"11","formattingOption":"relative","enabledLoadMore":"true","showDescription":"true","display1":"false","dateType":"updateOnly"}}service=content-feed'
            page_url = f'https://www.armytimes.com/pb/api/v2/render/feature/global/mco-results-list-load-more?contentConfig={param}'
            yield Request(url=page_url, callback=self.parse_item, dont_filter=True)

    def parse_item(self, response):
        response_html = response.json().get('rendering')
        element_html = etree.HTML(response_html)
        news_list = element_html.xpath('//a[@class="o-storyTease__link m-headlineTease__link"]/@href')
        for item in news_list:
            yield response.follow(url=item, callback=self.parse_content, dont_filter=True)

    # 解析详情页
    def parse_content(self, response):
        self.logger.info(f'详情页URL:{response.url}')
        extractor = GeneralNewsExtractor()
        extract_result = extractor.extract(html=response.text,
                                           with_body_html=True,
                                           noise_node_list=['//div[contains(@class,"o-articleBody__signupForm")]',
                                                            '//*[contains(@class,"m-headlineTease__info")]',
                                                            '//*[contains(@class,"m-aboutAuthor")]',
                                                            '//*[contains(@class,"o-articleBody__storyTease")]'],
                                           # title_xpath='//h1[contains(@class,"Heading__H1")]/text()',
                                           author_xpath='string(//*[@class="author-name addthis"])',
                                           # publish_time_xpath='string(//span[@itemprop="datePublished"])',
                                           # body_xpath='//*[@id="article-content"]'
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

        if news_publish_time:
            news_publish_time = format_date(news_publish_time)

        img_url = response.xpath('//img[@class="m-byline__featuredImage"]/@src').extract_first()
        img_describe = response.xpath('//figcaption[@class="m-byline__caption a-caption"]/text()').extract_first()
        img_data = []
        if img_url:
            img_name = f'news/img_{time.strftime("%Y_%m_%d_")}{bson.ObjectId()}.png'
            img_data = [{
                'img_url': img_url,
                'img_describe': img_describe,
                'img_name': img_name,
            }]

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
