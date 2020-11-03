#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  1 13:10:19 2019

@author: mints
"""
from lxml import html
from providers.tap import TAPLookup

class ObsLogLookup(TAPLookup):
    CATALOGS = {'ESOLog':
         {'url': "http://archive.eso.org/tap_obs",
          'columns': "dataproduct_type, dataproduct_subtype,facility_name, instrument_name, obs_collection, filter,access_estsize, access_url"},
         'Canadian': {'url': "http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/tap/",
                      'columns': "distinct obs_collection,facility_name,instrument_name,target_name"} #,obs_release_date,access_url"}
    }
    DEBUG = True

    def _prepare_sql(self, catalog, ra, dec, radius):
        param = self.CATALOGS[catalog]
        if 'table' in param:
            table = param['table']
        else:
            table = 'ivoa.Obscore'
        sql = f"""SELECT {param['columns']}
        FROM {table}
        WHERE CONTAINS(POINT('ICRS', {ra}, {dec}), s_region)=1"""
        if 'where' in param:
            sql = sql + ' AND ' + ' AND '.join(param['where'])
        return sql

    def _post_process_table(self, table):
        """
        First column contains references to full record on vizier - need
        to correct the URL there.
        """
        for element in table.xpath('//td'):
            if element.text is None:
                continue
            if element.text.startswith('http'):
                a = html.Element('a')
                a.attrib['href'] = element.text
                a.text = element.text
                element.append(a)
                element.text = None
        return table