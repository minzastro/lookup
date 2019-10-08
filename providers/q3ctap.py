#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  1 13:15:20 2019

@author: mints
"""
from providers.tap import TAPLookup

class Q3CTapLookup(TAPLookup):
    CATALOGS = {'des':
        {'url': "http://datalab.noao.edu/tap",
         'columns': "ra, dec, mag_auto_g, mag_auto_r, mag_auto_i",
         'table': 'des_dr1.main'
        }
    }

    def _prepare_sql(self, catalog, ra, dec, radius):
        param = self.CATALOGS[catalog]
        r = radius / 3600.
        constraints = ''
        if 'constraints' in param and len(param['constraints']) > 0:
            constraints = "AND " + 'AND'.join(param['constraints'])
        sql = f"""SELECT {param['columns']}, Q3C_DIST(ra, dec, {ra}, {dec})*3600.0 as distance
        FROM {param['table']} where 't' = Q3C_RADIAL_QUERY(ra, dec, {ra}, {dec}, {r})
        {constraints}
        order by distance
        """
        return sql
