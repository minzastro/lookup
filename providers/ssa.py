#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 09:48:40 2016

@author: mints
"""
from lxml import html
from astropy.coordinates import SkyCoord
from providers.basic import BasicLookup, _get_mags

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
        for cell in table.xpath('//td[contains(., "-9.99999")]'):
            cell.text = ''
        for cell in table.xpath('//td[contains(., "-99.99999")]'):
            cell.text = ''
        if len(table.getchildren()) == 0:
            return None
        head = table.getchildren()[0] #.getchildren()[0]
        head.getchildren()[1].text = 'Distance'
        #body = table.getchildren()[1]
        for row in table.getchildren()[1:]:
            ra = float(row.getchildren()[2].text)
            de = float(row.getchildren()[3].text)
            c = SkyCoord(ra, de, unit="deg")
            cell = row.getchildren()[1]
            cell.text = (c.separation(self.center)*3600).to_string(decimal=True)
            cell.remove(cell.getchildren()[0])
        return table
