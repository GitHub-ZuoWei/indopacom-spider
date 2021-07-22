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


class NavySpider(scrapy.Spider):
    name = 'navy'
    start_urls = ['https://www.cpf.navy.mil/news.aspx/']

    # custom_settings = {
    #     'ITEM_PIPELINES': {'indopacom_spider.pipelines.SaveImagePipeline': 1,
    #                        'indopacom_spider.pipelines.IndopacomNewsSpiderPipeline': 300}
    # }

    def start_requests(self):
        # yield Request(url=self.start_urls, callback=self.parse, dont_filter=False,meta={'proxy': 'http://192.168.12.180:6666'})
        # 'https://www.pacom.mil/Media/News/?Page=11'

        yield Request(url=self.start_urls[0], callback=self.parse_item, dont_filter=True)

    # 解析列表页
    def parse_item(self, response):
        # 总页数
        page_sum = response.xpath('//*[@class="sm"][last()]/a/text()').extract_first()
        self.logger.info(f'新闻总页数为:{page_sum}')
        self.logger.info(f'列表页URL:{response.url}')

        news_list = response.xpath('//*[@class="news-story-content"]/a/@href').extract()
        for item in news_list:
            yield response.follow(url=item, callback=self.parse_content, dont_filter=False)

        # 获取下一页链接
        next_url = response.xpath("//ul[contains(@class,'pagination')]"
                                  "/li[contains(@class,'active')]"
                                  "/following-sibling::li[1]/a/@href").extract_first()
        if next_url:
            yield response.follow(url=next_url, callback=self.parse_item, dont_filter=True)

    # 解析详情页
    def parse_content(self, response):
        self.logger.info(f'详情页URL:{response.url}')

        # document = Document(response.text)
        # html_content = document.summary(html_partial=True)
        # content = etree.HTML(html_content).xpath('string(.)').strip()
        # pub_time = response.xpath('//div[@class="category-date"]/text()').extract()[1]

        extractor = GeneralNewsExtractor()
        extract_result = extractor.extract(html=response.text, with_body_html=True,
                                           author_xpath='//*[@class="byline"]/text()',
                                           publish_time_xpath='//*[@class="timestamp"]/text()',
                                           body_xpath='//*[@class="main"]')
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

        # 作者
        if news_author.startswith('By'):
            source = ''
            author = news_author.replace('By', '').strip()
        # 来源
        else:
            author = ''
            source = news_author.replace('From', '').strip()

        if news_publish_time:
            news_publish_time = format_date(news_publish_time.replace('Posted', '').strip())

        img_url_list = response.xpath('//img[@class="news-photo"]/@src').extract()

        img_describe_list = response.xpath('//p[@class="news-photo-caption__text"]/text()').extract()

        img_data = []
        for img_url, img_describe in zip(img_url_list, img_describe_list):
            img_data.append(
                {
                    "img_url": img_url,
                    "img_describe": img_describe.strip(),
                    # 不在正文中
                    "img_name": f'news/img_{time.strftime("%Y_%m_%d_")}{bson.ObjectId()}.png',
                }
            )

        # yield Request(url='http://www.baidu.com', callback=self.parse_img, dont_filter=True, meta={'item': item})
        yield IndopacomNewsSpiderItem(title=news_title_gne,
                                      publish_time=news_publish_time,
                                      author=format_author(author),
                                      content=news_content_gne,
                                      content_html=news_content_html_gne,
                                      source=source,
                                      keywords=[],
                                      categories=[],
                                      img_data=img_data,
                                      video_data=[],
                                      url=response.url,
                                      site_name=self.name,
                                      insert_time=time.strftime('%Y-%m-%d %H:%M:%S'))
