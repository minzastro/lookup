#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 25 17:21:20 2017

@author: mints
"""
from lxml import html
import requests as rq
from requests_toolbelt.multipart.encoder import MultipartEncoder
from providers.basic import BasicLookup


class MultipartLookup(BasicLookup):
    KEEP_PLAIN_HTML = False
    def _get_referer(self, catalog):
        return self.URL

    def _get_url(self, catalog, ra, dec, radius):
        return self.URL

    def _get_html_data(self, catalog, ra, dec, radius):
        payload = self._prepare_request_data(catalog, ra, dec, radius)
        multipart_data = MultipartEncoder(fields=payload)
        host = self.URL.split('/')[2]
        headers = {'Host': host,
                   'Origin': 'http://%s' % host,
                   'Referer': self._get_referer(catalog),
                   'Accept-Encoding': 'gzip, deflate',
                   'Content-Type': multipart_data.content_type}
        try:
            req = rq.post(self._get_url(catalog, ra, dec, radius),
                          data=multipart_data,
                          headers=headers, timeout=5)
        except rq.ReadTimeout:
            return html.fromstring('<TABLE border="1">')
        text = req.content
        if self.DEBUG:
            with open('%s.html' % catalog, 'wb') as f:
                f.write(text)
                f.close()
        if self.KEEP_PLAIN_HTML:
            return text
        else:
            return html.fromstring(text)
