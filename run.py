import sqlite3


from crawler import Crawler


def main():
    id_file = input('id file ("customer_ids"): ') or 'customer_ids'
    customer_ids = get_customer_ids(id_file)

    token_file = input('token(laravel_session, "token"): ') or 'token'
    token_file = open(token_file)
    token = token_file.read().strip()
    token_file.close()

    crawler = Crawler(token=token, customer_ids=customer_ids)
    crawler.run()


def get_customer_ids(id_file):
    f = open(id_file, 'r', 1)
    ids = f.read().split()
    f.close()
    return ids


if __name__ == '__main__':
    main()
