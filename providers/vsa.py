#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 09:48:40 2016

@author: mints
"""
from providers.basic import BasicLookup, _get_mags

class VSALookup(BasicLookup):

    CATALOGS = {'VHS': ('VHSDR3', 'VHSsource',
                        'sourceID,ra,dec,mergedClass,pStar,eBV,' +
                        _get_mags(['y', 'j', 'h', 'ks'])),
                'VIKING': ('VIKINGDR4', 'vikingSource',
                           'sourceID,ra,dec,mergedClass,pStar,eBV,' +
                           _get_mags(['z', 'y', 'j', 'h', 'ks'])),
                'VVV': ('VVVDR4', 'vvvSource',
                        'sourceID,ra,dec,mergedClass,pStar,' +
                        _get_mags(['z', 'y', 'j', 'h', 'ks'], 'AperMag3')),
                }

    URL = "http://horus.roe.ac.uk:8080/vdfs/WSASQL"
    XPATH = '//table[count(tr)>1]'

    def _prepare_request_data(self, catalog, ra, dec, radius):
        param = self.CATALOGS[catalog]
        payload = {'database': param[0],
                   'archive': 'VSA',
                   'formaction': 'region',
                   'from': param[1],
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
                   'select': param[2],
                   }
        return payload