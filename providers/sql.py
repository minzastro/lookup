#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 10:16:28 2016

@author: mints
"""
from providers.basic import BasicLookup
from lib.sql2file import sql_to_file
from lib.sqlconnection import SQLConnection
from lxml import html


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
        table.attrib['cellspacing'] = '0'
        return table
