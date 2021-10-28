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
import os
import uuid

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

    DEBUG = False

    KEEP_PLAIN_HTML = False

    REQUEST_PARAMS = {}

    def __init__(self):
        self.result_html = None

    def _brief_name(self):
        return self.__class__.__name__[:-6]

    def force_config_reload(self):
        jsonname = 'config/%s.json' % self._brief_name()
        if not os.path.exists(jsonname):
            self.force_config_dump()
        self.CATALOGS = json.load(open(jsonname, 'r'))

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

    def _wrap(self, base):
        wrapper = html.Element('div')
        uid = uuid.uuid4()
        button = html.Element('button')
        button.attrib['class'] = 'collapsible'
        button.text = "Open..."
        wrapper.append(button)
        wrapper.append(base)
        return wrapper
        #<button type="button" class="collapsible">Open Collapsible</button>


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
        req = rq.post(self.URL, params=self.REQUEST_PARAMS,
                      data=self._prepare_request_data(catalog, ra, dec,
                                                      radius))
        text = req.content
        if self.DEBUG:
            self._debug_save(text, 'debug_%s.html' % catalog)
        if self.KEEP_PLAIN_HTML:
            return text
        else:
            return html.fromstring(text)

    def _debug_save(self, page, filename):
        f = open(filename, 'wb')
        f.write(page)
        f.close()

    def load_data(self, catalog, ra, dec, radius):
        """
        Load data, extract html table and prepare output div.
        """
        self.result_html = self._get_html_data(catalog, ra, dec, radius)
        if self.result_html is None:
            # No data
            return '1%s' % catalog
        r = self.result_html.xpath(self.XPATH)
        if r is not None:
            if len(r) == 0:
                # No data
                return '1%s' % catalog
            base = self._build_basic_answer(catalog)
            r = self._post_process_table(r[0])
            if r is not None:
                # Some providers can be more complex than other.
                # Sometimes post-processing reveals that there is no data...
                base.append(r)
            else:
                # No data
                return '1%s' % catalog
        else:
            # No data
            return '1%s' % catalog
        return tostring(self._wrap(base), method='html')
