#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 09:48:40 2016

@author: mints
"""
from providers.basic import BasicLookup, _get_mags
from lib.html_addons import replace_empty

class VSALookup(BasicLookup):

    CATALOGS = {'VHS': {'database': 'VHSDR3',
                        'table': 'VHSsource',
                        'columns': 'sourceID,ra,dec,mergedClass,pStar,eBV,' +
                        _get_mags(['y', 'j', 'h', 'ks'])},
                'VIKING': {'database': 'VIKINGDR4',
                           'table': 'vikingSource',
                           'columns': 'sourceID,ra,dec,mergedClass,pStar,eBV,' +
                           _get_mags(['z', 'y', 'j', 'h', 'ks'])},
                'VVV': {'database': 'VVVDR4',
                        'table': 'vvvSource',
                        'columns': 'sourceID,ra,dec,mergedClass,pStar,' +
                        _get_mags(['z', 'y', 'j', 'h', 'ks'], 'AperMag3')},
                }

    URL = "http://horus.roe.ac.uk:8080/vdfs/WSASQL"
    XPATH = '//table[count(tr)>1]'

    def _prepare_request_data(self, catalog, ra, dec, radius):
        param = self.CATALOGS[catalog]
        payload = {'database': param['database'],
                   'archive': 'VSA',
                   'formaction': 'region',
                   'from': param['table'],
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
                   'rows': '5',
                   'select': param['columns'],
                   }
        return payload

    def _post_process_table(self, table):
        table = replace_empty(table, ['-9.999995E008'])
        return table
