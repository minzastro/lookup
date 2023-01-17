#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 10:02:47 2016

@author: mints
"""
from providers.basic import BasicLookup

class VizierLookup(BasicLookup):
    """
    Provider for Vizier data.
    """

    CATALOGS = {
      '2MASS': 'II/246/out',
      'AllWISE': 'II/328/allwise',
      'SDSS': 'V/139/sdss9',
      'GLIMPSE': 'II/293/glimpse',
      'PPMXL': 'I/317/sample',
      'NOMAD': 'I/297/out',
      'UKIDSS': 'II/319/las9',
      'APASS': 'II/336/apass9',
      'URAT1': 'I/329/urat1'
    }
    #DEBUG=True
    URL = 'http://cdsarc.u-strasbg.fr/viz-bin/VizieR'

    XPATH = '//div[@id="CDScore"]/table[@class="sort"]'

    def _prepare_request_data(self, catalog, ra, dec, radius):
        return {'-source': self.CATALOGS[catalog],
                '-out.add': '_r',
                '-c.ra': ra,
                '-c.dec': dec,
                '-c.rs': radius}

    def _post_process_table(self, table):
        """
        First column contains references to full record on vizier - need
        to correct the URL there.
        """
        for element in table.xpath('//a[@class="full"]'):
            element.attrib['href'] = 'http://cdsarc.u-strasbg.fr/viz-bin/' + \
                                     element.attrib['href']
        return table
