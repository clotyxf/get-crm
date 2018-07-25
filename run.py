import sqlite3


from crawler import Crawler


def main():
    id_file = input('id file ("customer_ids"): ') or 'customer_ids'
    customer_ids = get_customer_ids(id_file)

    token = input('token(laravel_session): ')
    token = 'eyJpdiI6IlhhVnRreWxrRkpXaWtPaEs0bW4xMFE9PSIsInZhbHVlIjoiUjZKUmt4Ynl6NHpaMDJnU0oxUENDR3lFSVZWRkhKNUVERTcwUkJFanJrTXpwK2h0SnRBaGlhNXRzUDZMQkJtRXMwR0xtVkIySmNieWFKbEhrVjRqVGc9PSIsIm1hYyI6IjYzZDllOTgxZjViYzcxMWUxMThlMGI0OTUxYmQ0NTdkN2VjM2U0ZGYyYjVhNTNhOTVhNjExMGZkZDFhNzdmNTYifQ%3D%3D'

    crawler = Crawler(token=token, customer_ids=customer_ids)
    crawler.run()


def get_customer_ids(id_file):
    f = open(id_file, 'r', 1)
    ids = f.read().split()
    print('Get customer ids finish.')
    return ids


if __name__ == '__main__':
    main()
