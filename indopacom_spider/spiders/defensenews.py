import time

import bson
import scrapy

from lxml import etree
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


class DefensenewsSpider(scrapy.Spider):
    name = 'defensenews'
    start_urls = ['https://www.defensenews.com/']

    def start_requests(self):
        self.logger.info(f'新闻总页数为:{100 / 10}')
        for page_num in range(0, 100, 10):
            self.logger.info(f'列表页URL:{(page_num / 10) + 1}')
            param = f'{{"_jge":"content-feed","Feed-Parameter":"/newsletters/daily-news-roundup","Feed-Limit":"10","Feed-Offset":{page_num}}}customFields={{"artworkPosition":"right","offset":"0","commentsCountCivil":"false","showAuthor":"true","showDate":"true","commentsCountDisqus":"false","numItems":"10","formattingOption":"relative","enabledLoadMore":"true","showDescription":"true","dateType":"displayOnly"}}service=content-feed'
            page_url = f'https://www.defensenews.com/pb/api/v2/render/feature/global/mco-results-list-load-more?contentConfig={param}'
            yield Request(url=page_url, callback=self.parse_item, dont_filter=True)

    def parse_item(self, response):
        response_html = response.json().get('rendering')
        element_html = etree.HTML(response_html)
        news_list = element_html.xpath('//div[@class="col-xs-4 art-right"]/a/@href')
        for item in news_list:
            yield response.follow(url=item, callback=self.parse_content, dont_filter=True)

    def parse_content(self, response):
        self.logger.info(f'详情页URL:{response.url}')

        document = Document(response.text)
        html_content = document.summary(html_partial=True)
        content = etree.HTML(html_content).xpath('string(.)').strip()

        extractor = GeneralNewsExtractor()
        extract_result = extractor.extract(html=response.text,
                                           with_body_html=True,
                                           noise_node_list=['//div[contains(@class,"List__Wrapper")]',
                                                            '//div[contains(@class,"default__Wrapper")]',
                                                            '//div[contains(@class," mco-body-item mco-body-type-interstitial_link")]',
                                                            '//div[contains(@class,"newsletter-subscribe")]',
                                                            '//div[contains(@class,"mco-body-type-image")]',
                                                            '//div[contains(@class,"InterstitialLink")]'],
                                           title_xpath='//h1[contains(@class,"Heading__H1")]/text()',
                                           author_xpath='string(//span[contains(@itemprop,"author")])',
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
        # news_content_gne = extract_result['content']
        # 新闻内容 HTML
        # news_content_html_gne = extract_result['body_html']

        if news_publish_time:
            news_publish_time = format_date(news_publish_time.strip())

        if not news_author:
            news_author = response.xpath('string(//span[contains(@class,"Byline__Author")])').extract_first()

        img_url = response.xpath('//img[@class="image-lazy"]/@src').extract_first()
        img_describe = response.xpath('//figcaption[@class="publish"]/h4/text()').extract_first()
        if not img_url and not img_describe:
            img_url = response.xpath(
                '//div[contains(@class,"ArticleHeader__LeadArtWrapper")]/link/@href').extract_first()
            img_describe = response.xpath('string(//figcaption[@class="a-caption"])').extract_first()
            if not img_url and not img_describe:
                img_url = response.xpath('//img[@class="m-byline__featuredImage"]/@src').extract_first()
                img_describe = response.xpath(
                    '//figcaption[@class="m-byline__caption a-caption"]/text()').extract_first()

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
                                      content=content,
                                      content_html=html_content,
                                      source='',
                                      keywords=[],
                                      categories=[],
                                      img_data=img_data,
                                      video_data=[],
                                      url=response.url,
                                      site_name=self.name,
                                      insert_time=time.strftime('%Y-%m-%d %H:%M:%S'))
