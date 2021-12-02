# -*- coding: utf-8 -*-
#
# indopacom_spider
# Author: ZuoWei
# Email: zuowei@yuchen.com
# Created Time: 2021/7/27 10:02
import os


def get_zip_file(input_path, result):
    files = os.listdir(input_path)
    for file in files:
        if os.path.isdir(input_path + '/' + file):
            get_zip_file(input_path + '/' + file, result)
        else:
            result.append(input_path + '/' + file)