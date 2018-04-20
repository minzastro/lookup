#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 16 17:54:23 2018

@author: mints
"""
import os
import simplejson as json
import numpy as np
from lxml import html
import requests as rq
from providers.basic import BasicLookup
from dl import authClient, queryClient
from astropy.table import Table
from astropy.io import votable
import tempfile
from lib.html_addons import add_distance_column
from astropy.coordinates import SkyCoord

class NOAOLookup(BasicLookup):
    LOGIN_FILE = 'providers/noao_login.json'
    XPATH = '//table'

    def __init__(self):
        if os.path.exists(self.LOGIN_FILE):
            try:
                login_data = json.load(open(self.LOGIN_FILE, 'r'))
                self.token = authClient.login(login_data['login'],
                                              password=login_data['password'])
                self.enabled = True
            except ImportError:
                self.enabled = False
        else:
            self.enabled = False

    def _query_to_votable(self, query):
        result = queryClient.query(self.token, adql=query, fmt='votable')
        with tempfile.TemporaryFile(mode='w+b') as f:
            for line in result:
                f.write(line.encode())
            f.seek(0)
            tbl = Table.read(f)
        return tbl

    def _get_html_data(self, catalog, ra, dec, radius):
        config = self.CATALOGS[catalog]
        self.center = SkyCoord(ra, dec, unit='deg')
        ra_radius = radius / np.cos(np.deg2rad(radius / 3600.)) / 3600.
        sql = f"""
        select {config['columns']} from {config['table']}
        where {config['ra']} between {ra - ra_radius} and {ra + ra_radius}
        and {config['dec']} between {dec - radius / 3600} and {dec + radius / 3600}
        """
        table = self._query_to_votable(sql)
        for column, pformat in config['formats']:
            table[column].format = pformat
        s = table.pformat(html=True, show_unit=False)
        return html.fromstring(' '.join(s))

    def _post_process_table(self, table):
        table.attrib['border'] = '1'
        table.attrib['cellspacing'] = '0'
        #html.tostring(table)
        if len(table.getchildren()) <= 1:
            return None
        table = add_distance_column(table, 1, 2, self.center,
                                    has_head=True, has_body=False)
        return table
