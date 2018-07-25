import sqlite3


class Db:
    db_name = 'data.db'

    def __init__(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
                       create table if not exists customer_info
                       (
                       id int primary key not null,
                       name varchar(30),
                       remarks text,
                       achives text
                       );
        ''')
        self.cursor.execute('''
                       create table if not exists wechat_message
                       (
                       custormer_id int primary key not null,
                       counselor_name varchar(30),
                       content text
                       );
        ''')
        self.cursor.execute('''
                       create table if not exists media
                       (
                       id integer primary key autoincrement,
                       data blob
                       );
        ''')
        print('Create table finish.')

    def customer_count(self):
        self.cursor.execute('select count(*) from customer_info')
        count = self.cursor.fetchone()[0]
        return count


    def save_media(self, content):
        self.cursor.execute('insert into media(data) values (?)',
                            (content,))
        self.conn.commit()
        return self.cursor.lastrowid

    def save_info(self, id, name, remarks, achieves):
        self.cursor.execute('insert into customer_info(id, name, remarks, achives) values (?,?,?,?)',
                            (id, name, remarks, achieves))
        self.conn.commit()
