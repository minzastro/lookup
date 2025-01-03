#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 15:39:49 2019

@author: mints
"""
from providers.basic import BasicLookup
from lxml import html
from lxml.etree import tostring
from astroquery.utils.tap.core import TapPlus
from requests.exceptions import HTTPError

class TAPLookup(BasicLookup):
    CATALOGS = {}

    def __init__(self):
        super(TAPLookup, self).__init__()

    def _prepare_sql(self, catalog, ra, dec, radius):
        return ""

    def _update_table(self, table, catalog, ra, dec, radius):
        return table

    def load_data(self, catalog, ra, dec, radius):
        param = self.CATALOGS[catalog]
        tap = TapPlus(url=param['url'],
                      default_protocol_is_https=param['url'].startswith('https'))
        sql = self._prepare_sql(catalog, ra, dec, radius)
        if sql is None:
            raise Exception('Prepare SQL not implemented')
        try:
            job = tap.launch_job(sql)
        except HTTPError as ex:
            print(catalog, sql)
            print(param)
            raise ex

        result = job.get_data()
        result = self._update_table(result, catalog, ra, dec, radius)
        if result is None:
            # No data
            return {'status': 204, 'html': 'No data'}
        if len(result) == 0:
            # No data
            return {'status': 204, 'html': 'No data'}
        base = self._build_basic_answer(catalog)
        table = html.fromstring(' '.join(result.pformat(html=True,
                                                        max_lines=-1,
                                                        max_width=-1)[:-1]))
        table.attrib['border'] = '1'
        table.attrib['cellspacing'] = '0'
        table = self._post_process_table(table)
        base.append(table)
        print(catalog, len(result))
        return {'status': 200, 'html': tostring(base, method='html')}
