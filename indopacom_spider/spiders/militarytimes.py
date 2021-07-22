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


class MilitarytimesSpider(scrapy.Spider):
    name = 'militarytimes'
    start_urls = ['https://www.militarytimes.com/news/']

    def start_requests(self):
        self.logger.info(f'新闻总页数为:{100 / 10}')
        for page_num in range(0, 100, 10):
            self.logger.info(f'列表页URL:{(page_num / 10) + 1}')
            param = f'{{"_jge":"content-feed","Feed-Parameter":"/news","Feed-Limit":"10","Feed-Offset":{page_num}}}customFields={{"artworkPosition":"right","offset":"0","commentsCountCivil":"false","showAuthor":"true","display2":"false","showDate":"true","commentsCountDisqus":"false","numItems":"15","formattingOption":"relative","enabledLoadMore":"true","showDescription":"true","display1":"false","dateType":"displayOnly"}}service=content-feed'
            page_url = f'https://www.militarytimes.com/pb/api/v2/render/feature/global/mco-results-list-load-more?contentConfig={param}'
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
                                                            '//*[contains(@class,"o-articleBody__storyTease")]'],
                                           author_xpath='string(//*[@class="author-name addthis"])',
                                           # publish_time_xpath='//*[@class="entry-date"]/text()',
                                           # body_xpath='//*[@class="main"]'
                                           )
        # # 新闻作者
        news_author = extract_result['author'].strip()
        # # 新闻发布时间
        news_publish_time = extract_result['publish_time'].strip()
        # # 新闻标题
        news_title_gne = extract_result['title']
        # # 新闻内容
        news_content_gne = extract_result['content']
        # # 新闻内容 HTML
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
