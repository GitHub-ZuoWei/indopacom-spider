from scrapy import cmdline

# cmdline.execute("scrapy crawl pacom".split())               1
# cmdline.execute("scrapy crawl navy".split())               1
# cmdline.execute("scrapy crawl usni".split())                 1
# cmdline.execute("scrapy crawl militarytimes".split())       1
# cmdline.execute("scrapy crawl c4isrnet".split())            1
# cmdline.execute("scrapy crawl defensenews".split())        1
# cmdline.execute("scrapy crawl stripes".split())             1
# cmdline.execute("scrapy crawl military".split())              1
# cmdline.execute("scrapy crawl armytimes".split())           1
# cmdline.execute("scrapy crawl hearings".split())
cmdline.execute("scrapy crawl breakingdefense".split())
