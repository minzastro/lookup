#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  1 13:15:20 2019

@author: mints
"""
import numpy as np
from providers.tap import TAPLookup
import astropy.units as u
from astropy.coordinates import SkyCoord

class BoxTapLookup(TAPLookup):
    """
    This lookup uses simplest box selection for
    maximum compatibility,
    but filters by real radius in post-processing.
    """
    CATALOGS = {'SSA':
        {'url': "http://wfaudata.roe.ac.uk/ssa-dsa/TAP",
         'columns': "objID,ra, dec, classMagB, classMagR1, classMagR2",
         'table': 'source',
         'constraints': ['Nplates > 0']
        }
    }

    def _update_table(self, table, catalog, ra, dec, radius):
        if len(table) == 0:
            return table
        c = SkyCoord(ra=ra*u.degree, dec=dec*u.degree)
        catalog = SkyCoord(ra=table['ra'], dec=table['dec'])
        table['distance'] = catalog.separation(c).arcsec
        mask = catalog.separation(c) < radius * u.degree
        table = table[mask]
        table.sort('distance')
        return table

    def _prepare_sql(self, catalog, ra, dec, radius):
        param = self.CATALOGS[catalog]
        r = radius / 3600.
        r1 = r / np.cos(dec)
        constraints = ''
        if 'constraints' in param and len(param['constraints']) > 0:
            constraints = "AND " + 'AND'.join(param['constraints'])
        if 'ra_dec' in param.keys():
            pos_constraint = f"""{param['ra_dec'][0]} between {ra - r1} and {ra + r1}
          and {param['ra_dec'][1]} between {dec - r} and {dec + r}"""
        else:
            pos_constraint = f"""ra between {ra - r1} and {ra + r1}
          and dec between {dec - r} and {dec + r}"""
        sql = f"""SELECT {param['columns']}
        FROM {param['table']}
        where {pos_constraint}
        {constraints}
        """
        print(catalog, sql)
        return sql
