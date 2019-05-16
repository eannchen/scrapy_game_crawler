import scrapy
import re
from bs4 import BeautifulSoup
import time
import random


def get_url_by_page(page: int and str) -> str:
    # 台中市
    # 其它軟體及網路相關業/數位內容產業/多媒體相關業/網際網路相關業/電腦軟體服務業
    return 'https://www.104.com.tw/cust/list/index/?page=%s&order=1&mode=s&jobsource=checkc&area=6001008000&indcat=1001001006,1001001005,1001001004,1001001003,1001001002' % page


class GameCropsItem(scrapy.Item):
    name = scrapy.Field()
    employees = scrapy.Field()
    vacancies = scrapy.Field()


class GameCropsSpider(scrapy.Spider):
    name = 'game_crops'
    allowed_domains = ['www.104.com.tw']
    start_urls = [get_url_by_page(1)]

    def __do_sleep(self):
        time.sleep(random.randint(0, 5))
        pass

    def parse(self, response):
        # for Test
        # request = scrapy.Request(get_url_by_page(1),
        #                          callback=self.parse_company_list,
        #                          dont_filter=True)
        # yield request

        main = BeautifulSoup(response.body, 'html.parser').find('main')

        # 總頁數
        page_total = main.find(id='company-pages').find(
            class_='page-total').attrs['data-total']
        # 每頁 request、解析
        for count in range(int(page_total)):
            page = count + 1
            if (page == 1):
                yield self.parse_company_list(response)
            else:
                request = scrapy.Request(get_url_by_page(page),
                                         callback=self.parse_company_list,
                                         dont_filter=True)
                self.__do_sleep()
                yield request

    # 公司清單頁
    def parse_company_list(self, response):
        main = BeautifulSoup(response.body, 'html.parser').find('main')

        # 公司清單
        companies = main.find(class_='company-summary').find_all('article')

        # 對每一公司頁 Request
        for company in companies:
            link = company.find('h1').a.attrs['href']
            request = scrapy.Request(link,
                                     callback=self.parse_company,
                                     dont_filter=True)
            self.__do_sleep()
            yield request

    # 公司內頁
    def parse_company(self, response):
        wrapper = BeautifulSoup(response.body,
                                'html.parser').find(id='wrapper')
        if not wrapper: return

        # 此公司資訊涵蓋範圍
        cont_main = wrapper.find(id='cont_main')

        # 遍歷頁面是否有「遊戲」字樣
        is_target = False
        for string in cont_main.stripped_strings:
            if (re.match(r'.*遊戲', string)):
                is_target = True
                break

        if (is_target):
            company = {}
            try:
                # 公司名稱
                company['name'] = wrapper.find(
                    id='comp_header').h1.string.strip()
            except Exception:  # 若含有暫無工作機會的訊息就跳過
                return

            # 員工人數
            company['employees'] = cont_main.find(
                'dt', string='員　　工：').find_next_sibling('dd').string

            # 職缺清單
            jobs = cont_main.find('form', attrs={
                'name': 'jobform'
            }).find_all(class_='joblist_cont')

            vacancies = []
            for job in jobs:
                job_name = job.find(class_='jobname').a.string.strip()
                vacancies.append(job_name)
            company['vacancies'] = '、'.join(vacancies)

            # End，丟至 GameCropsItem
            yield GameCropsItem(**company)
