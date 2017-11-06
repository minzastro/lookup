#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 13 11:31:42 2017

@author: mints
"""
import urllib
from lxml import html
import requests as rq
from providers.basic import BasicLookup


class DASCHLookup(BasicLookup):
    CATALOGS = {'DASCH': []}

    URL = "http://dasch.rc.fas.harvard.edu/lightcurve_cat_input.php"

    XPATH = '//pre'

    def _prepare_request_data(self, catalog, ra, dec, radius):
        return {'nmin': 1,
                'box': int(radius),
                'source': 'apass',
                'researcher': '',
                'coo': '%.2f %.2f' % (ra, dec),
                'tmpdirectory': '',
                'frameformat': 'tabs'}

    def _get_html_data(self, catalog, ra, dec, radius):
        """
        Get html page with data. Default option is POST request to URL.
        """
        req = rq.post('%s?%s' % (self.URL,
                                 urllib.parse.urlencode(
                                         self._prepare_request_data(
                                             catalog, ra, dec, radius))))
        text = req.content
        if self.DEBUG:
            self._debug_save(text, 'debug_%s.html' % catalog)
        return html.fromstring(text)

    def _post_process_table(self, table):
        """
        First column contains references to full record on vizier - need
        to correct the URL there.
        """
        if table.text_content().startswith('Data for this region is not available'):
            return None
        for element in table.xpath('//a'):
            element.attrib['href'] = 'http://dasch.rc.fas.harvard.edu/' + \
                                     element.attrib['href']
        return table
