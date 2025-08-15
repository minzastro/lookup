#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  1 13:15:20 2019

@author: mints
"""
from providers.basic import BasicLookup
from astroquery.vo_conesearch import conesearch
from lxml import html
from lxml.etree import tostring


class VizierVoLookup(BasicLookup):
    
    CATALOGS = {}

    def load_data(self, catalog, ra, dec, radius):
        """
        Load data, extract html table and prepare output div.
        """
        catname = self.CATALOGS[catalog]
        url = f'https://vizier.cds.unistra.fr/viz-bin/conesearch/{catname}?'
        search = conesearch.conesearch((ra, dec), radius / 3600., 
                                       catalog_db=url, return_astropy_table=True, verb=0)
        base = self._build_basic_answer(catalog)
        if search is None:
            # No data
            return {'status': 204, 'html': 'No data'}
        table = html.fromstring(' '.join(search.pformat(html=True,
                                                        max_lines=-1,
                                                        max_width=-1)[:-1]))
        table.attrib['border'] = '1'
        table.attrib['cellspacing'] = '0'
        table = self._post_process_table(table)
        base.append(table)
        print(catalog, len(search))
        return {'status': 200, 'html': tostring(base, method='html')}

