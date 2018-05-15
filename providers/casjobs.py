#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 19 14:38:54 2018

@author: mints
"""
import casjobs
import csv
from lxml import html
from providers.basic import BasicLookup


class CasJobsLookup(BasicLookup):
    KEEP_PLAIN_HTML = True
    XPATH = '//table'
    DEBUG = True

    def _get_auth(self, filename):
        lines = open(filename, 'r').readlines()
        return lines[0].strip(), lines[1].strip()

    def _get_html_data(self, catalog, ra, dec, radius):
        config = self.CATALOGS[catalog]
        auth = self._get_auth('providers/%s' % config[0])
        cas = casjobs.CasJobs(userid=auth[0], password=auth[1],
                              base_url=config[2])
        sql = config[3].format(ra, dec, radius)
        print(sql)
        output = cas.quick(sql, context=config[1])
        ihead = True
        rows = 0
        result = ['<TABLE border="1">']
        for row in csv.reader(output.split('\n')):
            if len(row) == 0:
                continue
            if row[0].strip().startswith('#'):
                continue
            if ihead:
                result.append('<TR>')
                result.extend(['<TH>%s</TH>' % item for item in row])
                result.append('</TR>')
                ihead = False
            else:
                rows = rows + 1
                result.append('<TR>')
                result.extend(['<TD>%s</TD>' % item for item in row])
                result.append('</TR>')
        result.append('</TABLE>')
        if rows == 0:
            return None
        return html.fromstring(' '.join(result))
