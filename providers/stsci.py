#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  2 12:00:20 2016

@author: mints
"""

from providers.basic import BasicLookup
import requests as rq
from lxml import html
from lib.html_addons import distance_column_arcsec

class STSCILookup(BasicLookup):

    CATALOGS = {"K2": {"url": "http://archive.stsci.edu/k2/data_search/search.php",
                       "full_url": "http://archive.stsci.edu/k2/data_search/search.php?target=&resolver=Resolve&radius={2}&ra={0}&dec={1}&" \
               "equinox=J2000&ktc_k2_id=&ktc_investigation_id=&twoMass=&kp=&" \
               "ktc_target_type%5B%5D=LC&ktc_target_type%5B%5D=SC&sci_campaign=&objtype=+&" \
               "extra_column_name_1=ktc_k2_id&extra_column_value_1=&extra_column_name_2=ktc_k2_id&extra_column_value_2=&extra_column_name_3=ktc_k2_id&extra_column_value_3=&extra_column_name_4=ktc_k2_id&extra_column_value_4=&" \
               "availableColumns=Mark&ordercolumn1=ang_sep&ordercolumn2=ktc_k2_id&ordercolumn3=&coordformat=dec&outputformat=HTML_Table&max_records=5001&max_rpp=500&" \
               "action=Search&selectedColumnsCsv=",
                       "columns": ['ktc_k2_id', 'sci_data_set_name',
                                   'sci_campaign', 'objtype',
                                   'sci_ra', 'sci_dec', 'ktc_target_type',
                                   'ktc_investigation_id', 'ang_sep',
                                   'rmag', 'e_rmag', 'jmag', 'e_jmag', 'kp',
                                   'kepflag', 'hip', 'tyc', 'sdss',
                                   'ucac', 'twomass', 'mflg', 'sci_module',
                                   'sci_output', 'sci_channel', 'k2_hlsp']},
                "HST": {"full_url": "https://archive.stsci.edu/hst/hsc_sum/search.php?" \
                    "action=Search&target=&resolver=Resolve&radius={2}&ra={0}&dec={1}&equinox=J2000&mag_type=xcat.SumMagAper2CatView&numimages=%3E+1&extra_column_name_1=matchid&extra_column_value_1=&extra_column_name_2=matchid&extra_column_value_2=&" \
                    "availableColumns=matchid&ordercolumn1=ang_sep&ordercolumn2=matchid&ordercolumn3=&coordformat=dec&outputformat=HTML_Table&remnull=on&max_records=5001&max_rpp=500&selectedColumnsCsv=",
                        "columns": ['matchid','numfilters','numvisits','numimages','targetname','matchra','matchdec','dsigma','abscorr','ang_sep']}
               }

    XPATH = '//table[@id="page"]'

    def _get_html_data(self, catalog, ra, dec, radius):
        """
        Get html page with data. Default option is POST request to URL.
        """
        url = self.CATALOGS[catalog]['full_url'] + '%2C'.join(self.CATALOGS[catalog]['columns'])
        req = rq.post(url.format(ra, dec, radius / 60.))
        text = req.content
        #self._debug_save(text, 'debug_%s.html' % catalog)
        return html.fromstring(text)

    def _bad_prepare_request_data(self, catalog, ra, dec, radius):
        par = {'action': 'Search',
               'availableColumns': 'Mark',
               'coordformat': 'dec',
               'dec': dec,
               'equinox': 'J2000',
               'extra_column_name_1': 'ktc_k2_id',
               'extra_column_name_2': 'ktc_k2_id',
               'extra_column_name_3': 'ktc_k2_id',
               'extra_column_name_4': 'ktc_k2_id',
               'extra_column_value_1': '',
               'extra_column_value_2': '',
               'extra_column_value_3': '',
               'extra_column_value_4': '',
               'kp': '',
               'ktc_investigation_id': '',
               'ktc_k2_id': '',
               'ktc_target_type[]': 'SC',
               'max_records': '5001',
               'max_rpp': '500',
               'objtype': '+',
               'ordercolumn1': 'ang_sep',
               'ordercolumn2': 'ktc_k2_id',
               'ordercolumn3': '',
               'outputformat': 'HTML_Table',
               'ra': ra,
               'radius': radius,
               'resolver': 'Resolve',
               'sci_campaign': '',
               'selectedColumnsCsv': 'ktc_k2_id,sci_data_set_name,sci_campaign,objtype,sci_ra,sci_dec,ktc_target_type,ktc_investigation_id,ang_sep,rmag,e_rmag,jmag,e_jmag,kp,kepflag,hip,tyc,sdss,ucac,twomass,mflg,sci_module,sci_output,sci_channel,k2_hlsp',
               'target': '',
               'twoMass': '' }
        return par

    def _post_process_table(self, table):
        table.attrib['border'] = '1'
        table.attrib['cellspacing'] = '0'
        if len(table.getchildren()) == 0:
            return None
        table.remove(table.getchildren()[-1])
        head = table.getchildren()[0]
        if len(head.getchildren()) > 1:
            head.remove(head.getchildren()[0])
        head.getchildren()[0].getchildren()[-1].text = '_r (arcsec)'
        for element in table.xpath('//a'):
            element.attrib['href'] = 'http://archive.stsci.edu/' + \
                                     element.attrib['href']
        table = distance_column_arcsec(table, -1, has_body=True)
        return table
