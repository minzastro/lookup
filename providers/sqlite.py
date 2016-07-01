#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 16:24:02 2016

@author: mints
"""
import os
from pysqlite2 import dbapi2 as sqlite3
from providers.basic import BasicLookup
from lxml import html

def _query_to_html(sql, conn):
    cursor = conn.execute(sql)
    result = ['<table><thead><tr>']
    for column in cursor.description:
        result.append('<th>%s</th>' % column[0])
    result.append('</tr></thead><tbody>')
    for row in cursor:
        result.append('<tr>')
        for item in row:
            result.append('<td>%s</td>' % item)
        result.append('</tr>')
    result.append('</tbody></table>')
    return '\n'.join(result)

class SQLiteLookup(BasicLookup):
    CATALOGS = {'Kharchenko': {'table': 'Kharchenko',
                               'ra': 'RAdeg', 'de': 'DEJ2000'}}
    XPATH = '//table[count(tbody/tr)>0]'

    def __init__(self):
        super(SQLiteLookup, self).__init__()
        self.conn = sqlite3.connect('%s/../data/data.sqlite' % os.path.dirname(__file__),
                                    check_same_thread=False)
        self.conn.enable_load_extension(True)
        self.conn.execute("select load_extension('%s/../sqlite_extentions/libsqlitefunctions.so')" % os.path.dirname(__file__))
        self.conn.enable_load_extension(False)

    def _get_html_data(self, catalog, ra, dec, radius):
        params = self.CATALOGS[catalog]
        sql = """select haversine({ra}, {de}, {ra_column}, {de_column}) as distance,
                        *
                   from {table}
                  where {de_column} between {de} - {radius} and {de} + {radius}
                    and haversine({ra}, {de}, {ra_column}, {de_column}) < {radius}"""
        table = _query_to_html(sql.format(ra=ra, de=dec, ra_column=params['ra'],
                                          de_column=params['de'],
                                          radius=radius/3600.,
                                          table=params['table']), self.conn)
        return html.fragment_fromstring(table)

    def _post_process_table(self, table):
        table.attrib['border'] = '1'
        table.attrib['cellspacing'] = '0'
        return table
