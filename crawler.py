import re

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
        customer_ids = self.customer_ids[start_index:]
        total = len(customer_ids)
        for i, customer_id in enumerate(customer_ids):
            print('[%d/%d] Pulling customer %s...' % (i+1, total, customer_id))

            # fetch info
            print('Fetch info...')
            info_html, customer_info = self.fetch_info(customer_id)

            # fetch message
            print('Fetch message...')
            message_list = []
            message_href = info_html.xpath('//a[contains(text(), "微信对话")]/@href')
            if len(message_href) > 0:
                message_list += self.fetch_message(customer_id, message_href[0])
            message_href = info_html.xpath('//a[contains(text(), "花镇客户通")]/@href')
            if len(message_href) > 0:
                url = 'http://2.crm.huazhen.com' + message_href[0]
                message_list += self.fetch_message(customer_id, url)

            # save
            print('Saving to database...')
            self.db.save_info(**customer_info)
            for message in message_list:
                self.db.save_message(**message)
            print('done.')

        print('All done!!')

    def fetch_info(self, customer_id):
        r = requests.get('http://2.crm.huazhen.com/sells/%s' % (customer_id,),
                         headers = self.headers)
        html = string_to_html(r.text)

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
                    if not img_src.startswith('http'):
                        img_src = 'http://2.crm.huazhen.com' + img_src
                    media_id = self.save_media(img_src)
                    img_element.set('src_id', str(media_id))
                    img_element.set('src', None)

            achieves += element_to_string(achieves_element)

        customer_info =  {
            'id': customer_id,
            'name': name,
            'remarks': remarks,
            'achieves': achieves,
        }
        return html, customer_info

    def fetch_message(self, customer_id, url, will_fetch_others=True):
        if not url.startswith('http'):
            url = 'http://2.crm.huazhen.com' + url
        r = requests.get(url, headers = self.headers)
        html = string_to_html(r.text)

        # name
        tab_button_xpath = '/html/body/div[1]/div/section[2]/div/div'
        name_list = html.xpath(tab_button_xpath + '/a[contains(@class, "btn-primary")]/text()')
        if len(name_list) > 0:
            name = name_list[0]
        else:
            name = html.xpath(tab_button_xpath + '/a/text()')[0]
        print('  with %s' % (name,))

        # content
        content = ''
        message_elements = html.xpath('//div[contains(@class, "direct-chat-text")]')
        for element in message_elements:
            parent_class = element.getparent().get('class')
            if parent_class.find('direct-chat-msg') > 0 and parent_class.find('right') > 0:
                content += '<div class="right">'
            else:
                content += '<div>'

            children = element.getchildren()
            if len(children) > 0:
                e = children[0]
                src = e.get('src', 'null')
                if not src or src == 'null':
                    e.getparent().remove(e)
                else:
                    media_id = self.save_media(src)
                    e.set('src_id', str(media_id))
                    e.set('src', None)
                    content += element_to_string(e)
            else:
                content += element.text.strip()

            content += '</div>'

        if will_fetch_others:
            message_list = []
            message_list.append({
                'customer_id': customer_id,
                'counselor_name': name,
                'content': content,
            })
            counselor_hrefs = html.xpath(tab_button_xpath + '/a/@href')
            for href in counselor_hrefs[1:]:
                m = self.fetch_message(customer_id, href, False)
                message_list.append(m)
            return message_list
        else:
            return {
                'customer_id': customer_id,
                'counselor_name': name,
                'content': content,
            }

    def save_media(self, url):
        print('    pulling media %s' % (url,))
        id = -1
        try:
            r = requests.get(url, headers=self.headers)
            id = self.db.save_media(r.content)
        except requests.exceptions.MissingSchema as e:
            print(e.message)
        return id


def pick_up_value(html, xpath):
    l = html.xpath(xpath)
    return l[0].strip() if len(l) > 0 else ''


def pick_up_element(html, xpath):
    e = html.xpath(xpath)
    return element_to_string(e[0]) if len(e)>0 else ''


def element_to_string(element):
    return etree.tostring(element, encoding='utf-8').decode('utf-8')


def string_to_html(string):
    string = re.sub(u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD\U00010000-\U0010FFFF]+', '', string)
    return fromstring(string)

