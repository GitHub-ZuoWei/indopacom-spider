# -*- coding: utf-8 -*-
#
# indopacom_spider
# Author: ZuoWei
# Email: zuowei@yuchen.com
# Created Time: 2021/7/13 13:14
import re


# def format_text(string_text):
#     if not string_text.strip():
#         return ''
#     # \s 查找空白字符(空格符，制表符\t，回车符\r，换行符\n，垂直换行符\v，换页符\f)
#     result = re.sub(r'[\S]', ' ', string_text, re.I)
#     return result.strip()


def format_text(string_text):
    if not string_text.strip():
        return ''
    # \s 查找空白字符(空格符，制表符\t，回车符\r，换行符\n，垂直换行符\v，换页符\f)
    # result = re.sub(r'[\S]', ' ', string_text, re.I)  不好使
    return string_text.replace('\n', '').replace('\t', '')


a = '''
									
										Gary M.
									
									
										Brito, USA
									
									'''

# print(format_text(a))
