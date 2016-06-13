#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 11:43:48 2016

@author: mints
"""

import requests as rq
from lxml import html
import simplejson as json
from providers.basic import BasicLookup
import os

class LoginLookup(BasicLookup):
    """
    For sites that require log-in.
    """

    LOGIN_URL = ''
    LOGIN_FILE = ''

    def __init__(self):
        self.session = rq.Session()
        req = self.session.get(self.LOGIN_URL)
        text = req.content
        if os.path.exists(self.LOGIN_FILE):
            login_data = json.load(open(self.LOGIN_FILE, 'r'))
            payload = {'username': login_data['login'],
                       'password': login_data['password']}
            payload.update(self.get_login_payload(html.fromstring(text)))
            req = self.session.get(self.LOGIN_URL, params=payload)
            self.post_login_hook()
            self.enabled = True
        else:
            self.enabled = False

    def get_login_payload(self, page):
        return {}

    def post_login_hook(self):
        pass

    def load_data(self, catalog, ra, dec, radius):
        if self.enabled:
            return super(LoginLookup, self).load_data(catalog, ra, dec, radius)
        else:
            base = html.Element('div')
            header = html.Element('h2')
            header.text = '%s is disabled (no login provided)' % catalog
            base.append(header)
            return html.tostring(base)

