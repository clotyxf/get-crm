import sqlite3

from crawler import Crawler

from settings import SETTINGS


def main():
    f = open(SETTINGS['id_filename'])
    customer_ids  = f.read().split()
    f.close()

    f = open(SETTINGS['token_filename'])
    token = f.read().strip()
    f.close()

    crawler = Crawler(token=token, customer_ids=customer_ids)
    crawler.run()


if __name__ == '__main__':
    main()
