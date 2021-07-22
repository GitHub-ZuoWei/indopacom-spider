# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


# 新闻、官网类 Item
class IndopacomNewsSpiderItem(scrapy.Item):
    title = scrapy.Field()
    publish_time = scrapy.Field()
    author = scrapy.Field()
    content = scrapy.Field()
    content_html = scrapy.Field()
    source = scrapy.Field()
    keywords = scrapy.Field()
    categories = scrapy.Field()
    img_data = scrapy.Field()
    video_data = scrapy.Field()
    url = scrapy.Field()
    site_name = scrapy.Field()
    insert_time = scrapy.Field()


# 听证会 Item
class IndopacomHearingSpiderItem(scrapy.Item):
    title = scrapy.Field()
    publish_time = scrapy.Field()
    location = scrapy.Field()
    agenda = scrapy.Field()
    witnesses = scrapy.Field()
    member_statements = scrapy.Field()
    related_file = scrapy.Field()
    video_data = scrapy.Field()
    url = scrapy.Field()
    site_name = scrapy.Field()
    insert_time = scrapy.Field()
    person_name_list = scrapy.Field()
    file_url_list = scrapy.Field()
