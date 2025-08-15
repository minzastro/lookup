#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 17:41:20 2016

@author: mints
"""
from lxml import html
from requests_toolbelt.multipart.encoder import MultipartEncoder
from providers.login import LoginLookup
from lib.html_addons import add_distance_column
from astropy.coordinates import SkyCoord

class ESOLookup(LoginLookup):
    XPATH = '//table'

    CATALOGS = {'KIDS': {'id': 53,
                         'fields': [1, 2, 3, 7, 130, 131, 132, 133,
                                    122, 123, 124, 125],
                         'fields_total': 155,
                         'constraints': {}},
                'VPHAS': {'id': 59,
                          'fields': [1, 2, 3, 15, 16, 29, 30, 43, 44,
                               56, 57, 69, 70, 83, 84, ],
                          'fields_total': 99,
                          'constraints': {6: '=1'}},
                'ATLAS': {'id': 66,
                          'fields': [1, 5, 6, 29, 30, 31, 32, 33, 34,
                               40, 41, 63, 64, 86, 87, 109, 110,
                               132, 133, 155],
                          'fields_total': 155,
                          'constraints': {11: '=0'}}}

    LOGIN_URL = 'https://www.eso.org/sso/login?service=https%3A%2F%2Fwww.eso.org%3A443%2FUserPortal%2Fsecurity_check'
    LOGIN_FILE = 'providers/eso_login.json'
    ESO_URL = 'https://www.eso.org/sso/login'

    def get_login_payload(self, page):
        form = page.xpath('//form')[0]
        return {'execution': form.xpath('//input[@name="execution"]')[0].value,
                'service': 'https://www.eso.org:443/UserPortal/security_check',
                '_eventId': 'submit'}

    def post_login_hook(self):
        req = self.session.post('https://www.eso.org/sso/login?service=http%3A%2F%2Fwww.eso.org%2Fqi%2Fsecurity_check')
        if self.DEBUG:
            self._debug_save(req.content, 'ESO.html')

    def _get_html_data(self, catalog, ra, dec, radius):
        param = self.CATALOGS[catalog]
        self.center = SkyCoord(ra, dec, unit='deg')
        _ = self.session.post('https://www.eso.org/qi/catalogQuery/index/%s?' % param['id'])
        url = 'https://www.eso.org/qi/catalogQuery/search/%s' % param['id']
        fields = ''.join([',row_%s_%s' % (param['id'], item)
                          for item in param['fields']])
        payload = {
            'target': '%s %s' % (ra, dec),
            'epoch': 'J2000',
            'radius': str(radius),
            'radiusUnit': 'arcsec',
            'radiusType': 'Cone',
            'searchGeoButton': 'Search & Download',
            'exportFormatSpatial': 'HTML',
            'exportFormat': 'FITS',
            'constraintTitleOld': '',
            'columnOrder': '',
            '_action_exportSpatial': 'Search',
            'selectedFields_%s' % param['id']: fields,
            'targetFileName': ('filename', '', 'application/octet-stream')
        }
        for i in range(1, param['fields_total']+1):
            if i in param['constraints']:
                payload['param_%s_%s' % (param['id'], i)] = param['constraints'][i]
            else:
                payload['param_%s_%s' % (param['id'], i)] = ''
        multipart_data = MultipartEncoder(fields=payload)
        headers = {
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.eso.org/qi/catalogQuery/index/%s?' % param['id'],
            'Connection': 'keep-alive',
            'Content-Type': multipart_data.content_type
        }
        req = self.session.post(url, headers=headers, data=multipart_data)
        text = req.content
        if self.DEBUG:
            self._debug_save(text, 'debug_%s.html' % catalog)
        return html.fromstring(text)

    def _post_process_table(self, table):
        table.attrib['border'] = '1'
        table.attrib['cellspacing'] = '0'
        if len(table.getchildren()) == 0:
            return None
        table = add_distance_column(table, 2, 3, self.center, has_head=True,
                                    has_body=True)
        return table
