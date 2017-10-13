#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 09:48:40 2016

@author: mints
"""
from providers.basic import BasicLookup
from lib.html_addons import replace_empty, distance_column_arcsec


class WSALookup(BasicLookup):
    CATALOGS = {'UKIDSS_LAS': '101',
                'UKIDSS_GPS': '102'}

    URL = "http://wsa.roe.ac.uk:8080/wsa/WSASQL"
    XPATH = '//table[count(tr)>1]'

    def _prepare_request_data(self, catalog, ra, dec, radius):
        param = self.CATALOGS[catalog]
        payload = {'database': 'UKIDSSDR10PLUS',
                   'programmeID': param,
                   'formaction': 'region',
                   'from': 'source',
                   'ra': ra,
                   'dec': dec,
                   'sys': 'J',
                   'xSize': '',
                   'ySize': '',
                   'name': '',
                   'radius': radius/60.,
                   'boxAlignment': 'RADec',
                   'emailAddress': '',
                   'format': 'HTML',
                   'compress': 'GZIP',
                   'rows': '10',
                   'select': 'default',
                   'where': 'priOrSec = 0'
                   }
        return payload

    def _post_process_table(self, table):
        table = replace_empty(table, ['-9.999995E008'])
        table = distance_column_arcsec(table, -1)
        return table
