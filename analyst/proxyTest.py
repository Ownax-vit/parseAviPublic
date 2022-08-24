import time
from queue import Queue
from analyst.crawlers import CrawlerAvitoSelenMultipleProxyAsync

# URL = "http://getip.ru/"
# URL = "https://www.avito.ru/"
URL = "https://www.avito.ru/belgorod/sport_i_otdyh/drugoe-ASgBAgICAUTKAuIK?" \
      "q=%D0%BC%D0%B5%D1%82%D0%B0%D0%BB%D0%BB%D0%BE%D0%B8%D1%81%D0%BA%D0%B0%D1%82%D0%B5%D0%BB%D1%8C"

def main():

    queueItem = Queue()
    # queueProxy = Queue() не реализован
    crawler = CrawlerAvitoSelenMultipleProxyAsync(URL)
    # crawler = CrawlerAvitoSelen(URL)
    crawler.crawl(queueItem)

if __name__ == '__main__':
    main()