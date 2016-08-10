#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 09:48:40 2016

@author: mints
"""
from lxml import html
from providers.basic import BasicLookup, _get_mags
from lib.html_addons import replace_empty, add_distance_column
from astropy.coordinates import SkyCoord

class SSALookup(BasicLookup):

    CATALOGS = {'SSA': {'columns': 'default'},
                }

    URL = "http://ssa.roe.ac.uk:8080/ssa/SSASQL"
    XPATH = '//table[count(tr)>1]'

    def _prepare_request_data(self, catalog, ra, dec, radius):
        self.center = SkyCoord(ra, dec, unit='deg')
        param = self.CATALOGS[catalog]
        payload = {'server': 'amachine',
                   'action': 'radial',
                   'ra': ra,
                   'dec': dec,
                   'sys': 'J',
                   'name': '',
                   'radius': radius / 60.,
                   'emailAddress': '',
                   'format': 'HTML',
                   'compress': 'GZIP',
                   'rows': '30',
                   'select': param['columns'],
                   'from': 'source',
                   'where': ''}
        return payload

    def _post_process_table(self, table):
        if len(table.getchildren()) == 0:
            return None
        table = replace_empty(table, ['-9.99999', '-99.99999'])
        table = add_distance_column(table, 2, 3, self.center, new_location=1)
        return table
