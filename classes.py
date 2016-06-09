#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 11:56:47 2016

@author: mints
"""
import requests as rq
from lxml import html
from lxml.etree import tostring
from lib.sql2file import sql_to_file
from lib.sqlconnection import SQLConnection


class BasicLookup(object):
    CATALOGS = {}

    DEFAULT_RADIUS = 10.

    URL = ''

    XPATH = ''

    def _build_basic_answer(self, catalog):
        base = html.Element('div')
        header = html.Element('h2')
        header.text = catalog
        base.append(header)

    def _prepare_request_data(self, catalog, ra, dec, radius):
        return {}

    def _post_process_table(self, table):
        return table

    def _get_html_data(self, catalog, ra, dec, radius):
        req = rq.post(self.URL,
                      data=self._prepare_request_data(catalog, ra, dec,
                                                      radius))
        text = req.text
        return html.fromstring(text)

    def load_data(self, catalog, ra, dec, radius):
        h = self._get_html_data(catalog, ra, dec, radius)
        r = h.xpath(self.XPATH)
        base = self._build_basic_answer(catalog)
        if len(r) == 0:
            div = html.Element('div')
            div.text = 'Nothing for %s' % catalog
            base.append(div)
            return tostring(base)
        r = r[0]
        r = self._post_process_table(r)
        base.append(r)
        return tostring(base)


class VizierLookup(BasicLookup):
    CATALOGS = {
      '2MASS': 'II/246/out',
      'AllWISE': 'II/328/allwise',
      'SDSS': 'V/139/sdss9',
      'GLIMPSE': 'II/293/glimpse',
      'PPMXL': 'I/317/sample',
      'NOMAD': 'I/297/out',
      'UKIDSS': 'II/319/las9',
      'APASS': 'II/336/apass9',
      'URAT1': 'I/329/urat1'
    }

    URL = 'http://vizier.u-strasbg.fr/viz-bin/VizieR'

    XPATH = '//div[@id="CDScore"]/table[@class="sort"]'

    def _prepare_request_data(self, catalog, ra, dec, radius):
        return {'-source': self.CATALOGS[catalog],
                '-out.add': '_r',
                '-c.ra': ra,
                '-c.dec': dec,
                '-c.rs': radius}

    def _post_process_table(self, table):
        for element in table.xpath('//a[@class="full"]'):
            element.attrib['href'] = 'http://vizier.u-strasbg.fr/viz-bin/' + \
                                     element.attrib['href']
        return table


def _get_mags(maglist, prefix='PetroMag'):
    out = ['{0}{1},{0}{1}Err'.format(m, prefix) for m in maglist]
    return ','.join(out)


class VSALookup(BasicLookup):

    CATALOGS = {'VHS': ('VHSDR3', 'VHSsource',
                        'sourceID,ra,dec,mergedClass,pStar,eBV,' +
                        _get_mags(['y', 'j', 'h', 'ks'])),
                'VIKING': ('VIKINGDR4', 'vikingSource',
                           'sourceID,ra,dec,mergedClass,pStar,eBV,' +
                           _get_mags(['z', 'y', 'j', 'h', 'ks'])),
                'VVV': ('VVVDR4', 'vvvSource',
                        'sourceID,ra,dec,mergedClass,pStar,' +
                        _get_mags(['z', 'y', 'j', 'h', 'ks'], 'AperMag3')),
                }

    URL = "http://horus.roe.ac.uk:8080/vdfs/WSASQL"
    XPATH = '//table[count(tr)>1]'

    def _prepare_request_data(self, catalog, ra, dec, radius):
        param = self.CATALOGS[catalog]
        payload = {'database': param[0],
                   'archive': 'VSA',
                   'formaction': 'region',
                   'from': param[1],
                   'ra': ra,
                   'dec': dec,
                   'sys': 'J',
                   'xSize': '',
                   'ySize': '',
                   'name': '',
                   'radius': radius/60.,
                   'boxAlignment': 'RADec',
                   'emailAddress': '',
                   'format': 'HTML',
                   'compress': 'GZIP',
                   'rows': '5',
                   'select': param[2],
                   }
        return payload


class SQLLookup(BasicLookup):
    CONN = SQLConnection('x', database='sage_gap')

    CATALOGS = {'RAVE': ("""rave_obs_id,raveid,teff_K,eteff_K,logg_K,elogg_K,
                            met_n_K,emet_K,snr_K, algo_conv_k,
                            distancemodulus_binney,age,mass""",
                         'radeg', 'dedeg'),
                'APOGEE': ("""apogee_id,snr,teff, teff_err,logg,logg_err,
                              param_m_h,param_m_h_err,
                              param_alpha_m,param_alpha_m_err,
                              ak_wise,ak_targ""", 'ra', '"dec"'),
                'GAIA_ESO': ("""cname,ges_fld,object,teff,e_teff,logg,e_logg,
                                feh,e_feh,j_vista,h_vista,k_vista""",
                             'ra', 'declination'),
                'LAMOST_GAC': ("""spec_id,date,objid,objtype,teff,teff_err,
                                  logg,logg_err,feh,feh_err,dist_mod,
                                  ebv_sfd,ebv_phot""",
                               'ra', '"dec"'),
                'SEGUE': ("""specobjid,spectypehammer,teffadop,teffadopunc,
                             loggadop,loggadopunc,fehadop,fehadopunc,snr""",
                          'ra', '"dec"')
                }
    XPATH = '//table[count(tr)>0]'

    def _get_html_data(self, catalog, ra, dec, radius):
        param = self.CATALOGS[catalog]
        sql = """select to_char(q3c_dist({2}, {3}, {4}, {5})*3600,
                                '99.99') as distance, {0}
        from input_{1}
        where {3} between {5}-{6} and {5}+{6}
          and q3c_dist({2}, {3}, {4}, {5}) < {6}
          """.format(param[0], catalog, param[1], param[2],
                     ra, dec, radius/3600.)
        sql_to_file(sql, write_format='html',
                    output_name='temp_%s' % catalog,
                    connection=self.CONN, overwrite=True)
        return html.parse('temp_%s.html' % catalog)

    def _post_process_table(self, table):
        table.attrib['border'] = '1'
        return table
