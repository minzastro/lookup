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
from astropy.coordinates import SkyCoord

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
        login_data = json.load(open(self.LOGIN_FILE, 'r'))
        payload = {'username': login_data['login'],
                   'password': login_data['password']}
        payload.update(self.get_login_payload(html.fromstring(text)))
        print payload
        req = self.session.get(self.LOGIN_URL, params=payload)
        print req, self.session.cookies
        self.post_login_hook()

    def get_login_payload(self, page):
        return {}

    def post_login_hook(self):
        pass