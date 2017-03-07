#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 10:16:28 2016

@author: mints
"""
from providers.basic import BasicLookup
import csv
from lxml import html
import requests as rq
from requests_toolbelt.multipart.encoder import MultipartEncoder


class ChinaVOLookup(BasicLookup):
    XPATH = '//table'
    DEBUG = True
    CATALOGS = {
          "scuss": {'url': 'scuss',
            'fields': [
            "catalogue.id",
            "catalogue.ra",
            "catalogue.dec",
            "catalogue.mag.auto",
            "catalogue.magerr.auto",
            "catalogue.psfadd",
            "catalogue.psfadderr",
            "catalogue.psfaddflag",
            "catalogue.modeladd",
            "catalogue.modeladderr"
          ]},
          "scuss-proper-motion": {'url': 'scuss-proper-motion',
            'fields': [
            "proper_motion.id",
            "proper_motion.ra",
            "proper_motion.dec",
            "proper_motion.pmra",
            "proper_motion.pmdec",
            "proper_motion.type"
          ]},
          "bassdr1gradd": {'url': 'bassdr1gradd',
            'fields': [
            "catalog.id",
            "catalog.ra",
            "catalog.dec",
            "catalog.mag_auto_g",
            "catalog.magerr_auto_g",
            "catalog.psfmag_g",
            "catalog.psfmagerr_g",
            "catalog.type_auto_g",
            "catalog.mag_auto_r",
            "catalog.magerr_auto_r",
            "catalog.psfmag_r",
            "catalog.psfmagerr_r",
            "catalog.type_auto_r"
          ]},
          "bass": {'url': 'general/bass/catalog',
            'fields': [
            "catalog.bassid",
            "catalog.ra",
            "catalog.dec",
            "catalog.mag_auto",
            "catalog.magerr_auto",
            "catalog.psfmag",
            "catalog.psfmagerr",
            "catalog.modelmag",
            "catalog.modelmagerr"
          ]}
        }

    def _get_html_data(self, catalog, ra, dec, radius):
        payload = {'pos.type': 'pos.cone',
                        'pos.cra': str(ra),
                        'pos.cdec': str(dec),
                        'pos.cradius': str(radius),
                        'setmaxrows': '1',
                        'maxrows': '20',
                        }
        payload = payload.items()
        xcatalog = self.CATALOGS[catalog]
        for column in xcatalog['fields']:
            payload.extend([('showcol', column),
                            ('%s.min' % column, ''),
                            ('%s.max' % column, '')
                            ])
        print payload
        multipart_data = MultipartEncoder(fields=payload)
        headers = {'Host': 'explore.china-vo.org',
                   'Origin': 'http://explore.china-vo.org',
                   'Referer': 'http://explore.china-vo.org/data/%s/f' % xcatalog['url'],
                   'Accept-Encoding': 'gzip, deflate',
                   'Content-Type': multipart_data.content_type
                        }
        result = ['<TABLE border="1">']
        try:
            req = rq.post('http://explore.china-vo.org/data/%s/buildre.csv' % xcatalog['url'],
                          data=multipart_data, headers=headers, timeout=5)
        except rq.ReadTimeout:
            return html.fromstring(' '.join(result))
        text = req.content
        f = open('%s.csv' % catalog, 'w')
        f.write(text)
        f.close()
        csv_reader = csv.reader(text.split('\n'))
        ihead = True
        rows = 0
        for row in csv_reader:
            if len(row) == 0:
                continue
            if row[0].strip().startswith('#'):
                continue
            if ihead:
                result.append('<TR>')
                result.extend(['<TH>%s</TH>' % item for item in row])
                result.append('</TR>')
                ihead = False
            else:
                rows = rows + 1
                result.append('<TR>')
                result.extend(['<TD>%s</TD>' % item for item in row])
                result.append('</TR>')
        return html.fromstring(' '.join(result))

    def _post_process_table(self, table):
        if len(table.getchildren()) < 2:
            return None
        else:
            return table
