import bson
import time

import scrapy
from requests_html import HTMLSession

from scrapy import Request, signals

from indopacom_spider.items import IndopacomHearingSpiderItem
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


# https://www.armed-services.senate.gov/hearings?PageNum_rs=1&
class HearingsSpider(scrapy.Spider):
    name = 'hearings'
    start_urls = ['https://www.armed-services.senate.gov/hearings?PageNum_rs=1&']

    # 初始化request_html 莫得办法:(   得用同步请求
    session = HTMLSession()

    custom_settings = {
        'ITEM_PIPELINES': {
            'indopacom_spider.pipelines.SaveFilesPipeline': 1,
            'indopacom_spider.pipelines.IndopacomHearingSpiderPipeline': 300
        }
    }

    def start_requests(self):
        # yield Request(url=self.start_urls, callback=self.parse, dont_filter=False,meta={'proxy': 'http://192.168.12.180:6666'})
        # 'https://www.pacom.mil/Media/News/?Page=11'

        yield Request(url=self.start_urls[0], callback=self.parse_item, dont_filter=True)

    # 解析列表页
    def parse_item(self, response):
        # 总页数
        page_sum = response.xpath('(//select[@class="span4"])[1]/option[last()]/text()').extract_first()
        self.logger.info(f'新闻总页数为:{page_sum}')
        self.logger.info(f'列表页URL:{response.url}')

        # 找 class="divider congress" 后面所有tr
        news_list = response.xpath('//tr[@class="divider congress"]/following-sibling::tr//a/@href').extract()

        for item in news_list:
            yield response.follow(url=item.strip(), callback=self.parse_content, dont_filter=False)

        # 获取下一页链接
        next_url = response.xpath("(//li[@class='next'])[last()]/a/@href").extract_first()
        if next_url:
            yield response.follow(url=next_url, callback=self.parse_item, dont_filter=True)

    # 解析详情页
    def parse_content(self, response):
        # 用于存放文件URL 传递给FilesPipeline下载
        pdf_url_list = []
        # 格式化人物名称
        person_name_list = []
        self.logger.info(f'详情页URL:{response.url}')

        title = response.xpath('(//div[@id="main_column"]/h1/text())[last()]').extract_first().strip()
        date = response.xpath('string(//span[contains(@class,"date")])').extract_first()
        __time = response.xpath('string(//span[contains(@class,"time")])').extract_first()
        location = response.xpath('string(//span[contains(@class,"location")])').extract_first()
        video_url = response.xpath('//iframe[contains(@class,"streaminghearing")]/@src').extract_first()
        publish_time = format_date(f"{date.replace('Date: ', '').strip()}, {__time.replace('Time: ', '').strip()}")

        # content = response.xpath(
        #     '//p[contains(@class,"hearing-meta")]/following-sibling::*/*[not(@class="streaminghearing") and not(name()="script")]').xpath(
        #     'string(.)').extract()

        # Agenda
        agenda = '<br>'.join(response.xpath('//div[@class="agenda"]//*[not(name()="h1")]/text()').extract())

        # Member Statements 和 Witnesses 的内容
        witnesses = []
        member_statements = []
        section_list = response.xpath('//div[@id="main_column"]/section')
        for section in section_list:
            section_name = section.xpath('h1/text()').extract_first().strip()
            element_vcard_list = section.xpath('ol/li[@class="vcard"]')
            for element_vcard in element_vcard_list:
                person_name = ' '.join(''.join(element_vcard.xpath('span/text()').extract()).split())
                format_name = ' '.join(''.join(element_vcard.xpath('span[@class="fn"]/text()').extract()).split())
                title = element_vcard.xpath('./div[@class="title"]/text()').extract_first()
                file_name = element_vcard.xpath('ul/li/a/text()').extract()
                file_url = element_vcard.xpath('ul/li/a/@href').extract()

                # PDF文件
                file = []
                for __name, __url in zip(file_name, file_url):
                    file_location_name = f'pdf/pdf_{time.strftime("%Y_%m_%d_")}{bson.ObjectId()}.pdf'
                    file.append({
                        'file_name': __name.strip(),
                        'file_url': __url,
                        'file_location_name': file_location_name
                    })
                    # PDF 文件下载
                    pdf_html = self.session.get(__url)
                    pdf_url = pdf_html.html.xpath('//div[@class="row"]//a/@href', first=True)
                    if pdf_url:
                        pdf_url_list.append({
                            'file_name': __name.strip(),
                            'file_url': pdf_url,
                            'file_location_name': file_location_name
                        })

                # 入 witnesses list
                if section_name == 'Witnesses':
                    witnesses.append({
                        'person_name': person_name,
                        'title': title,
                        'file': file,
                    })
                # 入 member_statements list
                else:
                    member_statements.append({
                        'person_name': person_name,
                        'title': title,
                        'file': file,
                    })
                # 格式化的人名
                # rule_replace = ['Senator','']
                person_name_list.append(format_name.replace('Senator', '').split(',')[0].strip())

        # 网页右上角的相关文件
        related_file = []
        related_files_name = response.xpath('//aside[@class="files"]/ul/li/a/text()').extract_first()
        related_files_url = response.xpath('//aside[@class="files"]/ul/li/a/@href').extract_first()
        if related_files_name and related_files_url:
            file_location_name = f'pdf/pdf_{time.strftime("%Y_%m_%d_")}{bson.ObjectId()}.pdf'
            related_file.append({
                'file_name': related_files_name.strip(),
                'file_url': related_files_url,
                'file_location_name': file_location_name
            })
            # PDF 文件下载
            pdf_html = self.session.get(related_files_url)
            pdf_url = pdf_html.html.xpath('//div[@class="row"]//a/@href', first=True)
            if pdf_url:
                pdf_url_list.append({
                    'file_name': related_files_name,
                    'file_url': pdf_url,
                    'file_location_name': file_location_name
                })

        # 视频描述
        video_data = []
        if video_url:
            video_data.append({
                "video_url": video_url.split('&poster')[0],
                "video_describe": '',
                "video_name": '',
            })

        # 异步下载文件不好使
        # item = IndopacomHearingSpiderItem(title=title, publish_time=publish_time,
        #                                   location=location.replace('Location: ', '').strip(), agenda=agenda,
        #                                   witnesses=witnesses, member_statements=member_statements,
        #                                   related_file=related_file, video_data=video_data, url=response.url,
        #                                   site_name=self.name, insert_time=time.strftime('%Y-%m-%d %H:%M:%S'))
        # for file_item in self.pdf_url:
        #     requests = response.follow(url=file_item['file_url'],
        #                                callback=self.parse_file, dont_filter=True)
        #     requests.meta['item'] = item
        #     yield requests

        yield IndopacomHearingSpiderItem(title=title, publish_time=publish_time,
                                         location=location.replace('Location: ', '').strip(), agenda=agenda,
                                         witnesses=witnesses, member_statements=member_statements,
                                         related_file=related_file, video_data=video_data, url=response.url,
                                         site_name=self.name, insert_time=time.strftime('%Y-%m-%d %H:%M:%S'),
                                         person_name_list=person_name_list,
                                         file_url_list=pdf_url_list)

    # def parse_file(self, response):
    #     item = response.meta['item']
    #     item['pdf_download_url'] = self.pdf_download_url
    #     pdf_url = response.xpath('//div[@class="row"]//a/@href').extract_first()
