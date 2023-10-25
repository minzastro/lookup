#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 17:29:50 2019

@author: mints
"""
import numpy as np
from providers.basic import BasicLookup

class OGLELookup(BasicLookup):
    CATALOGS = {'OGLE': {}}

    XPATH = "//table[@border='1']"
    URL = "http://ogledb.astrouw.edu.pl/~ogle/OCVS/query.php"
    REQUEST_PARAMS = {'qtype': 'bvi', 'first': 1}

    def _prepare_request_data(self, catalog, ra, dec, radius):
        ra_r = radius / (3600. * np.cos(np.deg2rad(dec)))
        return {'db_target': 'all',
                'val_targetSMC': 'on',
                'val_targetLMC': 'on',
                'val_targetBLG': 'on',
                'val_targetGD': 'on',
                'val_targetGAL': 'on',
                'sort': 'field',
                'disp_ra': 'on',
                'use_ra': 'on',
                'valmin_ra': ra - ra_r,
                'valmax_ra': ra + ra_r,
                'disp_decl': 'on',
                'use_decl': 'on',
                'valmin_decl': dec - radius / 3600.,
                'valmax_decl': dec + radius / 3600.,
                'disp_vmean': 'on',
                'disp_v_i': 'on',
                'disp_imean': 'on',
                'disp_vsig': 'on',
                'disp_isig': 'on',
                'sorting': 'ASC',
                'pagelen': 50,
                'maxobj': 50}

    def _post_process_table(self, table):
        """
        First column contains references to full record on vizier - need
        to correct the URL there.
        """
        for element in table.xpath('//a'):
            element.attrib['href'] = 'http://ogledb.astrouw.edu.pl/~ogle/OCVS/' + \
                                     element.attrib['href']
        return table

