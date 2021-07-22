import time

import bson
import scrapy

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

"""
        ´´´´´´´´██´´´´´´´
        ´´´´´´´████´´´´´´
        ´´´´´████████´´´´
        ´´`´███▒▒▒▒███´´´´´
        ´´´███▒●▒▒●▒██´´´
        ´´´███▒▒▒▒▒▒██´´´´´
        ´´´███▒▒▒▒██´                      项目： news_spider
        ´´██████▒▒███´´´´´                 语言： Python3.8
        ´██████▒▒▒▒███´´                   框架： scrapy+mongo+minio
        ██████▒▒▒▒▒▒███´´´´                构建工具： webpack
        ´´▓▓▓▓▓▓▓▓▓▓▓▓▓▒´´                 版本控制： git
        ´´▒▒▒▒▓▓▓▓▓▓▓▓▓▒´´´´´              css预处理: less
        ´.▒▒▒´´▓▓▓▓▓▓▓▓▒´´´´´              代码风格：eslint-standard
        ´.▒▒´´´´▓▓▓▓▓▓▓▒                   编辑器： Pycharm
        ..▒▒.´´´´▓▓▓▓▓▓▓▒                  数据库:  芒果DB
        ´▒▒▒▒▒▒▒▒▒▒▒▒                      服务器端脚本: Python3.8
        ´´´´´´´´´███████´´´´´              author: ZuoWei
        ´´´´´´´´████████´´´´´´´
        ´´´´´´´█████████´´´´´´
        ´´´´´´██████████´´´´
        ´´´´´´██████████´´´
        ´´´´´´´█████████´´
        ´´´´´´´█████████´´´
        ´´´´´´´´████████´´´´´
        ________▒▒▒▒▒
        _________▒▒▒▒
        _________▒▒▒▒
        ________▒▒_▒▒
        _______▒▒__▒▒
        _____ ▒▒___▒▒
        _____▒▒___▒▒
        ____▒▒____▒▒
        ___▒▒_____▒▒
        ███____ ▒▒
        ████____███
        █ _███_ _█_███
——————————————————————————女神保佑，代码永无bug——————————————————————
"""


class UsniSpider(scrapy.Spider):
    name = 'usni'
    start_urls = ['http://news.usni.org/']

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse_item, dont_filter=True)

    # 解析列表页
    def parse_item(self, response):
        # 总页数
        page_sum = response.xpath('//ol[@class="wp-paginate font-inherit"]/li[last()-1]/a/text()').extract_first()
        self.logger.info(f'新闻总页数为:{page_sum}')
        self.logger.info(f'列表页URL:{response.url}')

        news_list = response.xpath('//h1[@class="entry-title"]/a/@href').extract()
        for item in news_list:
            yield response.follow(url=item, callback=self.parse_content, dont_filter=True)

        # 获取下一页链接
        next_url = response.xpath('//a[@class="next"]/@href').extract_first()
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
        extract_result = extractor.extract(html=response.text,
                                           with_body_html=True,
                                           noise_node_list=['//*[@class="usninews_sharethis"]',
                                                            '//*[@id="jp-relatedposts"]',
                                                            '//p[@class="wp-caption-text"]'],
                                           author_xpath='//*[@class="author"]/a/text()',
                                           publish_time_xpath='//*[@class="entry-date"]/text()',
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

        source = ''

        if news_publish_time:
            news_publish_time = format_date(news_publish_time.strip())

        # 关键词
        keywords = response.xpath('//div[@class="article-keywords"]/b/a/text()').extract()
        # 分类
        categories = response.xpath('//div[@class="article-categories"]/a/text()').extract()

        # print(categories)

        img_url_list = response.xpath('//div[@class="wp-caption aligncenter"]/a/img/@src').extract()
        img_describe_list = response.xpath('//div[@class="wp-caption aligncenter"]/p/text()').extract()
        img_data = []
        for img_url, img_describe in zip(img_url_list, img_describe_list):
            img_name = f'news/img_{time.strftime("%Y_%m_%d_")}{bson.ObjectId()}.png'
            img_data.append(
                {
                    "img_url": img_url,
                    "img_describe": img_describe.strip(),
                    "img_name": img_name
                }
            )
            news_content_html_gne = news_content_html_gne.replace(img_url, img_name)

        # yield Request(url='http://www.baidu.com', callback=self.parse_img, dont_filter=True, meta={'item': item})
        yield IndopacomNewsSpiderItem(title=news_title_gne,
                                      publish_time=news_publish_time,
                                      author=format_author(news_author),
                                      content=news_content_gne,
                                      content_html=news_content_html_gne,
                                      source=source,
                                      keywords=keywords,
                                      categories=categories,
                                      img_data=img_data,
                                      video_data=[],
                                      url=response.url,
                                      site_name=self.name,
                                      insert_time=time.strftime('%Y-%m-%d %H:%M:%S'))
