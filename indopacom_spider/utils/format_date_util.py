import time

from dateutil import parser


def format_date(string_date):
    """
    格式化时间
    """
    try:
        format_date = parser.parse(string_date)
    except:
        try:
            format_date = parser.parse(string_date, fuzzy=True)
        except:
            return time.strftime('%Y-%m-%d %H:%M:%S')
    return str(format_date).split('+')[0][:19]

# print(str(format_date('2021-07-13T20:44:01+00:00')))
# print(str(powerful_format_date('July 6, 2021')))
