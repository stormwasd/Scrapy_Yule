"""
@Description :
@File        : grasp_fun_youth
@Project     : Scrapy_YuLe
@Time        : 2022/4/11 16:22
@Author      : LiHouJian
@Software    : PyCharm
@issue       :
@change      :
@reason      :
"""


import scrapy
from scrapy.utils import request
from Scrapy_YuLe.items import ScrapyYuleItem
from Scrapy_YuLe import upload_file
from datetime import datetime


class GraspFunYouthSpider(scrapy.Spider):
    name = 'grasp_fun_youth'
    allowed_domains = ['fun.youth.cn']
    start_urls = ['http://fun.youth.cn/']
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
    }

    def start_requests(self):
        for i in range(1, 10):
            url = f'http://fun.youth.cn/gnzx/index_{i}.htm'
            req = scrapy.Request(url, callback=self.parse, dont_filter=True)
            yield req

    def parse(self, response):
        url_list = response.xpath("//ul[@class='tj3_1']/li/a/@href").extract()
        titles = response.xpath(
            "//ul[@class='tj3_1']/li/a/text()").extract()
        pub_time_list = response.xpath(
            "//ul[@class='tj3_1']/li/font/text()").extract()
        for i in range(len(url_list)):
            url = 'http://fun.youth.cn/gnzx' + url_list[i].lstrip('.')
            req = scrapy.Request(
                url, callback=self.parse_detail, dont_filter=True)
            news_id = request.request_fingerprint(req)
            title = titles[i]
            pub_time = pub_time_list[i]
            req.meta.update({"news_id": news_id})
            req.meta.update({"title": title})
            req.meta.update({"pub_time": pub_time.split(' ')[0]})
            yield req

    def parse_detail(self, response):
        news_id = response.meta['news_id']
        title = response.meta['title']
        pub_time = response.meta['pub_time']
        source = response.xpath(
            "//span[@id='source_baidu']/text()").extract_first().split('：')[1].strip()
        content = ''.join(response.xpath("//div[@id='container']").extract())
        content_img = response.xpath(
            "//div[@id='container']/div[@class='TRS_Editor']/p/img/@src").extract()
        if content_img:
            content_img_list = list()
            for index, value in enumerate(content_img):
                img_name = title + str(index)
                if value.startswith('.'):
                    res = upload_file.send_file(
                        'https://image11.m1905.cn/uploadfile' +
                        value.lstrip('.'),
                        img_name,
                        self.headers)
                else:
                    res = upload_file.send_file(value, img_name, self.headers)
                if res['msg'] == 'success':
                    content = content.replace(value, res['url'][0])
                    content_img_list.append(res['url'][0])
                else:
                    self.logger.info(f'内容图片 {value} 上传失败，返回数据：{res}')

            imgs = ','.join(content_img_list)
        else:
            imgs = None

        item = ScrapyYuleItem()
        item['news_id'] = news_id
        item['category'] = '娱乐'
        item['content_url'] = response.url
        item['title'] = title
        item['issue_time'] = pub_time
        item['title_image'] = None
        item['information_source'] = '娱乐频道'
        item['content'] = content
        item['source'] = source
        item['author'] = None
        item['images'] = imgs
        item['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        item['cleaning_status'] = 0
        self.logger.info(item)
        yield item


if __name__ == '__main__':
    import scrapy.cmdline as cmd
    cmd.execute(['scrapy', 'crawl', 'grasp_fun_youth'])
