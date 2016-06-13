#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 17:41:20 2016

@author: mints
"""
from lxml import html
from requests_toolbelt.multipart.encoder import MultipartEncoder
from providers.login import LoginLookup
from astropy.coordinates import SkyCoord

class ESOLookup(LoginLookup):
    XPATH = '//table'

    CATALOGS = {'KIDS': (53, [1, 2, 3, 7,
                              130, 131, 132, 133,
                              122, 123, 124, 125], 155, {}),
                'VPHAS': (59, [1, 2, 3, 15, 16, 29, 30, 43, 44,
                               56, 57, 69, 70, 83, 84, ], 99,
                              {6: '=1'}),
                'ATLAS': (66, [1, 5, 6, 29, 30, 31, 32, 33, 34,
                               40, 41, 63, 64, 86, 87, 109, 110,
                               132, 133, 155], 155, {11: '=0'})}

    LOGIN_URL = 'https://www.eso.org/sso/login?service=https%3A%2F%2Fwww.eso.org%3A443%2FUserPortal%2Fsecurity_check'
    LOGIN_FILE = 'providers/eso.json'
    ESO_URL = 'https://www.eso.org/sso/login'

    def get_login_payload(self, page):
        form = page.xpath('//form')[0]
        return {'lt': form.xpath('//input[@name="lt"]')[0].value,
                'service': 'https://www.eso.org:443/UserPortal/security_check',
                '_eventId': 'submit'}

    def post_login_hook(self):
        req = self.session.post('https://www.eso.org/sso/login?service=http%3A%2F%2Fwww.eso.org%2Fqi%2Fsecurity_check')

    def _get_html_data(self, catalog, ra, dec, radius):
        param = self.CATALOGS[catalog]
        self.center = SkyCoord(ra, dec, unit='deg')
        url = 'http://www.eso.org/qi/catalogQuery/search/%s' % param[0]
        fields = ''.join([',row_%s_%s' % (param[0], item)
                          for item in param[1]])
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
            'selectedFields_%s' % param[0]: fields,
            'targetFileName': ('filename', '', 'application/octet-stream')
        }
        for i in xrange(1, param[2]+1):
            if i in param[3]:
                payload['param_%s_%s' % (param[0], i)] = param[3][i]
            else:
                payload['param_%s_%s' % (param[0], i)] = ''
        multipart_data = MultipartEncoder(fields=payload)
        headers = {
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'http://www.eso.org/qi/catalogQuery/index/%s?' % param[0],
            'Connection': 'keep-alive',
            'Content-Type': multipart_data.content_type
        }
        req = self.session.post(url, headers=headers, data=multipart_data)
        text = req.content
        self._debug_save(text, '11.html')
        return html.fromstring(text)

    def _post_process_table(self, table):
        table.attrib['border'] = '1'
        table.attrib['cellspacing'] = '0'
        html.tostring(table)
        if len(table.getchildren()) == 0:
            return None
        head = table.getchildren()[0].getchildren()[0]
        th = html.Element('th')
        th.text = 'Distance'
        head.append(th)
        body = table.getchildren()[1]
        for row in body.getchildren():
            ra = float(row.getchildren()[1].text)
            de = float(row.getchildren()[2].text)
            c = SkyCoord(ra, de, unit="deg")
            td = html.Element('td')
            td.text = c.separation(self.center).to_string(decimal=True)
            row.append(td)
        return table
