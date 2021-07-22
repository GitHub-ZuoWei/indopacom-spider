# -*- coding: utf-8 -*-
#
# indopacom_spider
# Author: ZuoWei
# Email: zuowei@yuchen.com
# Created Time: 2021/7/13 13:14
import re


def format_author(string_author):
    if not string_author or not string_author.strip():
        return []
    result = re.split(r',|AND|and', string_author, re.I)
    return [item.strip() for item in result if item.strip() != '']


# print(format_author('Mike Yeo, Nigel Pittaway, Usman Ansari, Vivek Raghuvanshi and Chris Martin'))
