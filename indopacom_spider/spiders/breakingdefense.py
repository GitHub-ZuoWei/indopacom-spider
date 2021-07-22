import re
import time

import bson
import scrapy

from lxml import etree
from readability import Document
from gne import GeneralNewsExtractor

from scrapy import Request, signals, FormRequest

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


class BreakingdefenseSpider(scrapy.Spider):
    name = 'breakingdefense'
    # allowed_domains = ['breakingdefense.com']  不好使  辣子鸡 :<
    start_urls = ['https://www.breakingdefense.com/tag/wargames/']

    total_page_num = 2

    def start_requests(self):
        self.logger.info(f'新闻总页数为:{self.total_page_num}')
        yield Request(url=self.start_urls[0], callback=self.parse_request_param, dont_filter=True)

    def parse_request_param(self, response):
        html_with_param = response.xpath('//*[@id="bmdefense-global-scripts-js-extra"]/text()').extract_first()
        security_param = re.findall('"nonce":"(.*?)"', html_with_param, re.I)[0]

        for page_id in range(1, self.total_page_num + 1):
            form_data = {
                "action": "bm_ajax_load_more",
                "page": str(page_id),
                "query": {"tag": "wargames", "category_name": "", "tag_id": "2920", "paged": "0", "post__not_in": [],
                          "tag__in": [], "post_type": ""},
                "security": security_param
            }

            yield FormRequest(url='https://breakingdefense.com/wp-admin/admin-ajax.php',
                              formdata=form_data,
                              callback=self.parse_item,
                              dont_filter=True)

    def parse_item(self, response):
        self.logger.info(f'列表页URL:{response.url}')
        element_html = etree.HTML(response.json()['data'])
        news_list = element_html.xpath('//h3[@class="postTitle"]/a/@href')
        for item in news_list:
            if not item.startswith('https://breakingdefense.com/tag/'):
                yield response.follow(url=item, callback=self.parse_content, dont_filter=False)

    def parse_content(self, response):
        self.logger.info(f'详情页URL:{response.url}')

        document = Document(response.text)
        html_content = document.summary(html_partial=True)
        content = etree.HTML(html_content).xpath('string(.)').strip()

        extractor = GeneralNewsExtractor()
        extract_result = extractor.extract(html=response.text,
                                           with_body_html=True,
                                           noise_node_list=['//div[contains(@class,"sponsor-inline")]',
                                                            '//div[contains(@id,"attachment")]'],
                                           title_xpath='//h1[@class="postTitle"]/a/text()',
                                           author_xpath='//span[@class="postAuthor"]/a/text()',
                                           # publish_time_xpath='//*[@class="entry-date"]/text()',
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

        keywords = response.xpath('//div[@class="postFooter"]/ul/li/p/a/text()').extract()

        # gne 对于这个不好使 :(
        # https://breakingdefense.com/2021/06/cold-war-era-to-modern-mission-success-digital-engineering-transforms-the-b-52/
        if not news_content_html_gne.startswith('<div class="entry">') or not news_content_gne:
            news_content_html_gne = html_content
            news_content_gne = content

        img_url = response.xpath('//div[contains(@id,"attachment")]//img/@src').extract_first()
        img_describe = response.xpath(
            '//div[contains(@id,"attachment")]//p[contains(@id,"caption-attachment")]/text()').extract_first()
        if not img_url:
            img_url = response.xpath('//img[contains(@class,"wp-image-")]/@src').extract_first()
        img_data = []
        if img_url:
            img_name = f'news/img_{time.strftime("%Y_%m_%d_")}{bson.ObjectId()}.png'
            img_data = [{
                'img_url': img_url,
                'img_describe': img_describe if img_describe else '',
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
