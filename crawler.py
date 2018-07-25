import requests
from lxml import etree
from lxml.html.soupparser import fromstring


from db import Db


class Crawler:
    db = Db()

    def __init__(self, token, customer_ids):
        self.headers = { 'Cookie': 'laravel_session=%s' % (token,) }
        self.customer_ids = customer_ids

    def run(self):
        start_index = self.db.customer_count()
        for customer_id in self.customer_ids[start_index:]:
            self.fetch_info(customer_id)

    def fetch_info(self, customer_id):
        r = requests.get('http://2.crm.huazhen.com/sells/%s' % (customer_id,),
                         headers = self.headers)
        html = fromstring(r.text)

        # name
        name_raw = pick_up_value(html, '/html/body/div[1]/div[1]/section[2]/div[1]/div[2]/div/div/div[1]/div[2]/text()')
        name = name_raw[5:]

        # remarks
        remarks = 'Email:\n'
        remarks += pick_up_value(html, '//*[@id="email"]/@value')
        remarks += '\n性别:\n'
        remarks += pick_up_value(html, '//select[@id="gender"]/option[@selected]/text()')
        remarks += '\n月收入:\n'
        remarks += pick_up_value(html, '//select[@name="income"]/option[@selected]/text()')
        remarks += '\nQQ:\n'
        remarks += pick_up_value(html, '//*[@id="qq"]/@value')
        remarks += '\n年龄:\n'
        remarks += pick_up_value(html, '//select[@name="age"]/option[@selected]/text()')
        remarks += '\n情感状况:\n'
        remarks += pick_up_value(html, '//select[@id="affectivestatus"]/option[@selected]/text()')
        remarks += '\n工作行业:\n'
        remarks += pick_up_value(html, '//select[@id="job"]/option[@selected]/text()')
        remarks += '\n地区:\n'
        prefix = 'var city_id = "'
        city_index = r.text.find(prefix) + len(prefix)
        if r.text[city_index] != '0':
            remarks += r.text[city_index : city_index+6]
        remarks += '\n微信号:\n'
        remarks += pick_up_value(html, '//input[@name="wechat"]/@value')
        remarks += '\n备注:\n'
        remarks += pick_up_element(html, '/html/body/div[1]/div[1]/section[2]/form[1]/div/div/div/div/div[3]/div/div/div/div/div/table')

        # achieves
        achieves = ''
        achieves_list = html.xpath('//div[@id="emotion_show"]/div[@class="box-body"]/div/div[contains(@class, "panel-body")]')
        for achieves_element in achieves_list:
            # save media
            for img_element in achieves_element.xpath('.//img'):
                img_src = img_element.get('src', 'null')
                if not img_src or img_src == 'null':
                    img_element.getparent().remove(img_element)
                else:
                    media_id = self.save_media(img_src)
                    img_element.set('src_id', str(media_id))
                    img_element.set('src', None)

            achieves += element_to_string(achieves_element)

        self.db.save_info(id=customer_id,
                     name=name,
                     remarks=remarks,
                     achieves=achieves)
        print('Customer %s %s fetched.' % (customer_id, name))
        input('pause')

    def save_media(self, url):
        print(url)
        r = requests.get(url, headers=self.headers)
        id = self.db.save_media(r.content)
        return id


def pick_up_value(html, xpath):
    l = html.xpath(xpath)
    return l[0].strip() if len(l) > 0 else ''


def pick_up_element(html, xpath):
    e = html.xpath(xpath)
    return element_to_string(e[0]) if len(e)>0 else ''


def element_to_string(element):
    return etree.tostring(element, encoding='utf-8').decode('utf-8')
