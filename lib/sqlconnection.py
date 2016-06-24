#!/usr/bin/python
import time
import psycopg2
import logging
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED
from psycopg2.extras import DictCursor

class SQLConnection(object):
    """
    Class to simplify PostgreSQL access.
    """
    def __init__(self, name, schema='public', database='amints'):
        """
        """
        self.lastcount = 0
        self.in_transaction = False
        self.profile = False
        self.last_description = []
        self.conn = psycopg2.connect(database=database, user="mints")
        self._start_transaction()
        self.set_schema(schema)
        self.conn.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
        self.log = logging.getLogger('SQL')
        self.log.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)-6s: %(name)s - %(levelname)s - %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.log.addHandler(console_handler)

    def set_schema(self, schema):
        self.schema = schema
        self.conn.cursor().execute("set search_path to %s" % schema)
        self.conn.commit()

    def close(self):
        """
        Closing connection.
        """
        self.conn.close()

    def _start_transaction(self):
        """
        Custom implementation of "Start transaction".
        """
        try:
            self.conn.cursor().execute('BEGIN')
            self.autocommit = False
        except psycopg2.InternalError:
            self.conn.rollback()
            self.conn.cursor().execute('BEGIN')

    def start(self):
        """
        Begin transaction.
        """
        if not self.in_transaction:
            self._start_transaction()
        self.in_transaction = True

    def rollback(self):
        """
        Perform rollback.
        """
        self.conn.rollback()

    def commit(self, start=False):
        """
        Commit only if it is needed.
        """
        if self.profile:
            start = time.time()
        try:
            if self.in_transaction:
                self.conn.commit()
            self.in_transaction = False
            self.autocommit = True
        except psycopg2.InternalError as oerr:
            raise oerr
        if self.profile:
            print 'Time: %.3f SQL: COMMIT' % (time.time() - start)
        if start:
            self.start()

    def _execute_with_cursor(self, query, cursor):
        """
        Run the SQL statement and return it's result.
        Log (with profiling information, if required).
        """
        if self.profile:
            start = time.time()
        if query.strip()[-1:] != ';':
            query = query + ';'
        try:
            self.start()
            self.log.debug(query.replace('\n', ' '))
            result = cursor.execute(query)
            self.lastcount = result
            self.last_description = cursor.description
        except Exception as oerr:
            self.conn.rollback()
            self.log.error(query.replace('\n', ' '))
            self.log.error(oerr)
            raise oerr
        if self.profile:
            self.log.debug('Time: %.3f SQL: %s' % (time.time() - start,
                                                   query.replace('\n', ' ')))
        #else:
        #    self.log.debug(query.replace('\n', ' '))
        return result

    def execute(self, query):
        """
        Overriding execute method with logging.
        """
        cur = self.conn.cursor()
        result = self._execute_with_cursor(query, cur)
        cur.close()
        return result

    def _get_lastcount(self, cursor):
        """
        Get a number of rows in the last SELECT.
        """
        return cursor.rowcount

    def execute_set(self, query_set, quiet=True):
        """
        Execute several SQL statements and return the last result.
        """
        if not isinstance(query_set, list):
            if not isinstance(query_set, str):
                raise ValueError("Got %s instead of list of SQLs" %
                                 str(query_set))
            else:
                query_set = query_set.strip('; ').split(';')
        cursor = self.conn.cursor()
        self.lastcount = 0
        for query in query_set:
            self._execute_with_cursor(query, cursor)
        if self._get_lastcount(cursor) > 0 and not quiet:
            return cursor.fetchall()
        else:
            return []

    def exec_return(self, query, single_column=True,
                    default_result=None,
                    return_all=False):
        """
        Run a single query and return the first value from resultset.
        """
        result = []
        try:
            cursor = self.conn.cursor()
            self._execute_with_cursor(query, cursor)
            if return_all:
                result = cursor.fetchall()
            else:
                result = cursor.fetchone()
            if single_column:
                if result is None:
                    result = default_result
                elif return_all:
                    result = [res[0] for res in result]
                else:
                    result = result[0]
                if isinstance(result, long):
                    result = int(result)
        finally:
            cursor.close()
        return result

    def exec_all(self, query):
        return self.exec_return(query, single_column=False, return_all=True)

    def exec_dict(self, query, return_all=False):
        """
        Run a single query and return the first value from resultset as dict.
        """
        result = []
        try:
            cursor = self.conn.cursor(cursor_factory=DictCursor)
            self._execute_with_cursor(query, cursor)
            if return_all:
                result = cursor.fetchall()
            else:
                result = cursor.fetchone()
        finally:
            cursor.close()
        return result

    def established(self):
        """
        :returns: True if the connection is active.
        """
        if self.conn:
            return not self.conn.closed
        else:
            return False

    def call_procedure(self, procname):
        """
        Proper procedure call (for Monet/Postgres compatibility.)
        """
        cur = self.conn.cursor()
        self._execute_with_cursor('call %s' % procname, cur)
        cur.close()

    def cursor(self):
        """
        Simple alias for cursor().
        """
        return self.conn.cursor()

    def get_cursor(self, query):
        """
        Create and return a cursor for a given query.
        """
        cur = self.conn.cursor()
        self._execute_with_cursor(query, cur)
        return cur

    def execute_file(self, filename):
        """
        Execute SQL script from file.
        """
        commands = ' '.join(open(filename, 'r').readlines())
        self.execute_set(commands)

    def insert_hash(self, table, values):
        fields = []
        val = []
        for key, value in values.iteritems():
            fields.append(key)
            val.append(str(value))
        sql = "insert into %s (%s) values (%s)" % (table, ','.join(fields),
                                                   ','.join(val))
        self.execute(sql)