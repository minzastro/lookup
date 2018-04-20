#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 10:16:28 2016

@author: mints
"""
from providers.multipart import MultipartLookup
import csv
from lxml import html


class ChinaVOLookup(MultipartLookup):
    URL = 'http://explore.china-vo.org'
    KEEP_PLAIN_HTML = True
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

    def _get_referer(self, catalog):
        return 'http://explore.china-vo.org/data/%s/f' % self.CATALOGS[catalog]['url']

    def _get_url(self, catalog, ra, dec, radius):
        return 'http://explore.china-vo.org/data/%s/buildre.csv' % self.CATALOGS[catalog]['url']

    def _prepare_request_data(self, catalog, ra, dec, radius):
        payload = {'pos.type': 'pos.cone',
                   'pos.cra': str(ra),
                   'pos.cdec': str(dec),
                   'pos.cradius': str(radius),
                   'setmaxrows': '1',
                   'maxrows': '20'}
        payload = list(payload.items())
        xcatalog = self.CATALOGS[catalog]
        for column in xcatalog['fields']:
            payload.extend([('showcol', column),
                            ('%s.min' % column, ''),
                            ('%s.max' % column, '')
                            ])
        return payload

    def _get_html_data(self, catalog, ra, dec, radius):
        text = super(ChinaVOLookup, self)._get_html_data(catalog, ra, dec,
                                                         radius)
        csv_reader = csv.reader(text.decode('utf-8').split('\n'))
        ihead = True
        rows = 0
        result = ['<TABLE border="1">']
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
        result.append('</TABLE>')
        return html.fromstring(' '.join(result))

    def _post_process_table(self, table):
        if len(table.getchildren()) < 2:
            return None
        else:
            return table
