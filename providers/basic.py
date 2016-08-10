#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 11:56:47 2016

@author: mints
"""
from lxml import html
from lxml.etree import tostring
import requests as rq
import simplejson as json

def _get_mags(maglist, prefix='PetroMag'):
    out = ['{0}{1},{0}{1}Err'.format(m, prefix) for m in maglist]
    return ','.join(out)


class BasicLookup(object):
    """
    Basic class to look up data in surveys.
    """
    CATALOGS = {}

    # Default search radius
    DEFAULT_RADIUS = 10.

    # Data access url
    URL = ''

    # XPath of the data table in the page returned.
    XPATH = ''

    def _brief_name(self):
        return self.__class__.__name__[:-6]

    def force_config_reload(self):
        self.CATALOGS = json.load(open('config/%s.json' % self._brief_name(), 'r'))

    def force_config_dump(self):
        json.dump(self.CATALOGS, open('config/%s.json' % self._brief_name(), 'w'), indent=2)

    def _build_basic_answer(self, catalog):
        """
        Produce a basic "response" div.
        """
        base = html.Element('div')
        header = html.Element('h2')
        header.text = catalog
        base.append(header)
        return base

    def _prepare_request_data(self, catalog, ra, dec, radius):
        """
        Prepare data for the request to service.
        """
        return {}

    def _post_process_table(self, table):
        """
        Any post-processing goes here.
        """
        return table

    def _get_html_data(self, catalog, ra, dec, radius):
        """
        Get html page with data. Default option is POST request to URL.
        """
        req = rq.post(self.URL,
                      data=self._prepare_request_data(catalog, ra, dec,
                                                      radius))
        text = req.content
        #self._debug_save(text, 'debug_%s.html' % catalog)
        return html.fromstring(text)

    def _debug_save(self, page, filename):
        f = open(filename, 'w')
        f.write(page)
        f.close()

    def load_data(self, catalog, ra, dec, radius):
        """
        Load data, extract html table and prepare output div.
        """
        h = self._get_html_data(catalog, ra, dec, radius)
        r = h.xpath(self.XPATH)
        base = self._build_basic_answer(catalog)
        if len(r) == 0:
            # No data
            return '1%s' % catalog
        r = r[0]
        r = self._post_process_table(r)
        if r is not None:
            base.append(r)
        else:
            # No data
            return '1%s' % catalog
        return tostring(base)
