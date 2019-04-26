#!/usr/bin/env python
"""DbHandler methods like connecting and inserting
"""
import logging
import sys

import CommonFunctions

from abc import ABC, abstractmethod
from argparse import Namespace
from decimal import Decimal
from xml.etree.ElementTree import Element as XmlNode


class UnsupportedDbError(Exception):
    def __init__(self, db_product):
        super(UnsupportedDbError, self).__init__()
        self.db_product = db_product

    def __str__(self):
        return "Unsupported Db: %s" % self.db_product


class DbHandler(ABC):
    def __init__(self, args):
        self.args = args
        self.conn = None
        self.document_id = -1
        self.s_id = -1
        self.w_real_id = -1
        self.time_id = -1
        self.start_time = ''
        self.start_s_id = -1
        self.start_w_id = -1
        self.end_time = ''
        self.end_s_id = -1
        self.end_w_id = -1

    @staticmethod
    def get_handler(args):
        if args.db_product == 'postgresql':
            return PostgreSQLHandler(args)
        else:
            raise UnsupportedDbError(args.db_product)

    @staticmethod
    def parse_time(time_str: str):
        toks = time_str.split(':')
        hours = int(toks[0])
        days = hours // 24
        hours = hours % 24
        minutes = int(toks[1])
        seconds = Decimal(toks[2].replace(',', '.'))
        ret = ""
        if days > 0:
            ret = f"{days} "
        ret += f"{hours}:{minutes}:{seconds}"
        return ret

    @abstractmethod
    def admin_connect(self):
        return self.conn

    @abstractmethod
    def connect(self):
        """Connect to DB and return a DB connection

        Returns:
        [type]: [description]
        """
        return self.conn

    def execute(self, cmd: str, vars=None):
        cur = self.conn.cursor()
        logging.debug("Execute command: %s", cmd)
        cur.execute(cmd, vars)
        return cur

    @abstractmethod
    def is_db_present(self, db_name=None):
        if not db_name:
            db_name = self.args.db_name
        return False

    @abstractmethod
    def is_table_present(self, table_name):
        return False

    def create_db(self, db_name: str):
        """Create DB

        Args:
            db_name (str): DB name
        """
        logging.info("Creating DB %s", db_name)
        self.execute(
            'CREATE DATABASE %s;' % db_name)

    def ensure_table_words(self):
        table_name = f"words_{self.args.lang}"
        if self.is_table_present(table_name):
            return
        else:
            logging.info(f"Table {table_name} is not present, creating")
        self.execute(f"""
                CREATE TABLE {table_name} (
                    DocumentId int NOT NULL,
                    SentenceId int NOT NULL,
                    WordId int NOT NULL,
                    Word varchar(255) NOT NULL);""")
        self.execute(f"""
                ALTER TABLE {table_name} ADD PRIMARY KEY
                (DocumentId, SentenceId, WordId);""")

    def ensure_table_meta(self):
        table_name = "meta"
        if self.is_table_present(table_name):
            return
        else:
            logging.info(f"Table {table_name} is not present, creating")
        self.execute(f"""
                CREATE TABLE {table_name} (
                    DocumentId int NOT NULL,
                    Key varchar(255) NOT NULL,
                    Value varchar(255) NOT NULL);""")
        self.execute(f"""
                ALTER TABLE {table_name} ADD PRIMARY KEY
                (DocumentId, Key);""")

    def ensure_table_time(self):
        table_name = f"time_{self.args.lang}"
        if self.is_table_present(table_name):
            return
        else:
            logging.info(f"Table {table_name} is not present, creating")
        self.execute(f"""
                CREATE TABLE {table_name} (
                    DocumentId int NOT NULL,
                    TimeId int NOT NULL,
                    StartSentenceId int NOT NULL,
                    StartWordId int NOT NULL,
                    StartTime  interval NOT NULL,
                    EndSentenceId int NOT NULL,
                    EndWordId int NOT NULL,
                    EndTime interval NOT NULL
                    );""")
        self.execute(f"""
                ALTER TABLE {table_name} ADD PRIMARY KEY
                (DocumentId, TimeId, StartSentenceId);""")

    def prepare(self):
        try:
            self.connect()
        except:
            logging.warning("Cannot connect to DB: %s", sys.exc_info()[0])
            self.admin_connect()
            if self.is_db_present():
                logging.info(
                        "DB name %s is already present", self.args.db_name)
                logging.fatal("Unexpected error")
                raise
            else:
                self.create_db(self.args.db_name)
                self.connect()
        self.ensure_table_words()
        self.ensure_table_meta()
        self.ensure_table_time()

    def insert_table_words(
                self, table_name: str, doc_id, s_id, w_real_id, word: str):
        return self.execute(f"""
            INSERT INTO {table_name}
            SELECT %(doc_id)s, %(s_id)s, %(w_real_id)s, %(word)s
             FROM (SELECT 0 AS i) AS mutex LEFT JOIN {table_name}
             ON DocumentId = %(doc_id)s AND SentenceId = %(s_id)s
              AND WordId = %(w_real_id)s
            WHERE i=0 AND DocumentId IS NULL;
            """, {
                    'doc_id': doc_id, 's_id': s_id, 'w_real_id': w_real_id,
                    'word': word})

    def insert_table_meta(
                self, table_name: str, doc_id, key: str, value: str):
        return self.execute(f"""
            INSERT INTO {table_name}
            SELECT %(doc_id)s, %(key)s, %(value)s
             FROM (SELECT 0 AS i) AS mutex LEFT JOIN {table_name}
             ON DocumentId = %(doc_id)s AND Key = %(key)s
            WHERE i=0 AND DocumentId IS NULL;
            """, {
                    'doc_id': doc_id, 'key': key, 'value': value})

    def insert_table_time(
                self, table_name: str, doc_id, time_id,
                start_s_id, start_w_id, start_time,
                end_s_id, end_w_id, end_time):
        start_time = start_time
        return self.execute(f"""
            INSERT INTO {table_name}
            SELECT %(doc_id)s, %(time_id)s,
             %(start_s_id)s, %(start_w_id)s, %(start_time)s,
             %(end_s_id)s, %(end_w_id)s, %(end_time)s
             FROM (SELECT 0 AS i) AS mutex LEFT JOIN {table_name}
             ON DocumentId = %(doc_id)s AND TimeId = %(time_id)s
              AND StartSentenceId = %(start_s_id)s
            WHERE i=0 AND DocumentId IS NULL;
            """, {
                    'doc_id': doc_id, 'time_id': time_id,
                    'start_time': start_time,
                    'start_s_id': start_s_id, 'start_w_id': start_w_id,
                    'end_time': end_time,
                    'end_s_id': end_s_id, 'end_w_id': end_w_id})

    def write_node(self, node: XmlNode, parent_path: str, args: Namespace):
        if node.tag == 'document':
            self.document_id = int(node.attrib['id'])
        elif node.tag == 'time':
            if node.attrib['id'][-1] == 'S':
                self.time_id = int(node.attrib['id'][1:-1])
                self.start_time = DbHandler.parse_time(node.attrib['value'])
            else:
                table_name = f"time_{self.args.lang}"
                self.end_time = DbHandler.parse_time(node.attrib['value'])
                self.insert_table_time(
                    table_name,
                    self.document_id,
                    self.time_id,
                    self.start_s_id,
                    self.start_w_id,
                    self.start_time,
                    self.s_id,
                    self.w_real_id,
                    self.end_time)
                self.start_s_id = -1
        elif node.tag == 's':
            self.s_id = int(node.attrib['id'])
        elif node.tag == 'w':
            # w id looks like: 1.20
            #   the first part (before .) is s id (1)
            #   the second part (after .) is w real id (20)
            table_name = f"words_{self.args.lang}"
            w_id_token = node.attrib['id'].split('.')
            self.s_id = int(w_id_token[0])
            self.w_real_id = int(w_id_token[1])
            self.insert_table_words(
                    table_name, self.document_id,
                    self.s_id, self.w_real_id, node.text)
            if self.start_s_id < 0:
                self.start_s_id = self.s_id
                self.start_w_id = self.w_real_id
        elif parent_path.startswith('meta.'):
            table_name = "meta"
            if node.text:
                self.insert_table_meta(
                        table_name, self.document_id, node.tag, node.text)


class PostgreSQLHandler(DbHandler):
    psycopg2 = __import__('psycopg2')

    def __init__(self, args):
        super(PostgreSQLHandler, self).__init__(args)

    def admin_connect(self):
        credential = {'dbname': 'postgres'}
        if self.args.db_admin_password:
            credential['password'] = self.args.db_admin_password
        self.conn = self.psycopg2.connect(**credential)
        self.conn.autocommit = True
        return super(PostgreSQLHandler, self).connect()

    def connect(self):
        credential = {'dbname': self.args.db_name}

        if self.args.db_user:
            credential[''] = self.args.db_password
        if self.args.db_password:
            credential['password'] = self.args.db_password
        self.conn = self.psycopg2.connect(**credential)
        self.psycopg2
        self.conn.autocommit = True
        return super(PostgreSQLHandler, self).connect()

    def is_db_present(self, db_name=None):
        if not db_name:
            db_name = self.args.db_name
        self.execute(
                f"""SELECT datname FROM pg_catalog.pg_database
                 WHERE lower(datname) = lower('{db_name}')""")
        if self.conn.cursor().fetchone():
            return True
        return False

    def is_table_present(self, table_name):
        cur = self.execute(
                "SELECT EXISTS (SELECT 1"
                " FROM   information_schema.tables"
                f" WHERE  table_catalog = '{self.args.db_name}'"
                f" AND    table_name = '{table_name}');")
        return cur.fetchone()[0]


if __name__ == '__main__':
    CommonFunctions.run_doctest_and_quit_if_enabled()
