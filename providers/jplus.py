#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 15:17:28 2017

@author: mints
"""

from providers.basic import BasicLookup
import simplejson as json
import pandas as pd
from lxml import html
from lxml.etree import tostring


class JPlusLookup(BasicLookup):
    CATALOGS = {'JPLUS_dr1': []}

    URL = 'http://archive.cefca.es/catalogues/jplus-dr1/cone_query'

    KEEP_PLAIN_HTML = True

    def _prepare_request_data(self, catalog, ra, dec, radius):
        return {'ra': ra,
                'dec': dec,
                'radius': radius}

    def load_data(self, catalog, ra, dec, radius):
        """
        Load data, extract html table and prepare output div.
        """
        self.result_html = self._get_html_data(catalog, ra, dec, radius)
        r = json.loads(self.result_html.decode('utf-8'))
        if r is not None:
            if 'rows' not in r:
                # No data
                return '1%s' % catalog
            if not r['rows']:
                # No data
                return '1%s' % catalog
            base = self._build_basic_answer(catalog)
            base.append(html.fromstring(pd.DataFrame(r['rows']).to_html()))
            return tostring(base, method='html')
        else:
            # No data
            return '1%s' % catalog
