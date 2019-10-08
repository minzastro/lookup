#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 13 15:32:49 2017

@author: mints
"""
from lxml import html
from lxml.etree import tostring
from os import path
import numpy as np
from astropy.io import fits
from astropy.table import Table
import astropy.units as u
from astropy.coordinates import SkyCoord
from providers.basic import BasicLookup


def get_nearest(l, b, ra, dec):
    gc = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs')
    gal_coord = gc.transform_to('galactic')
    lx = l.searchsorted(gal_coord.l.degree)
    bx = b.searchsorted(gal_coord.b.degree)
    print(gal_coord, l[lx], b[bx])
    if np.abs(gal_coord.l.degree - l[lx]) > 1 or \
        np.abs(gal_coord.b.degree - b[bx]) > 1:
        return None
    elif np.abs(gal_coord.l.degree - l[lx]) > 0.5:
        return l[lx - 1], b[bx]
    elif np.abs(gal_coord.b.degree - b[bx]) > 0.5:
        return l[lx], b[bx - 1]
    else:
        return l[lx], b[bx]



class DECamLookup(BasicLookup):
    CATALOGS = {
        'DECaPS': {
            'url': 'https://faun.rc.fas.harvard.edu/decaps/release/band-merged/',
            'bricks': '/home/mints/data/DES/bricks_DECaPS.fits',
            'radius': 3.,
            'brick_file': 'decam_flux_{4}.fits'
            },
        'DECaLS': {
            'url': 'http://portal.nersc.gov/project/cosmo/data/legacysurvey/dr7/tractor/',
            'bricks': '../data/survey-bricks.fits.gz',
            'radius': 1.,
            'brick_file': ''

            }
        }
    DATA = None #fits.open('/home/mints/data/DES/bricks_DECaPS.fits')[1].data

    def __init__(self):
        super(DECamLookup, self).__init__()

    def _get_brick_filename(self, l, b):
        if b < 0:
            return 'decam_flux_l%0.1fbm%0.1f.fits' % (l, -b)
        else:
            return 'decam_flux_l%0.1fb%0.1f.fits' % (l, b)

    def _coord_search(self, ra, dec, filename, radius, best=False):
        local_data = fits.open(filename)[1].data
        mask = np.logical_and(
                    np.logical_and(local_data['ra'] > ra - radius / np.cos(dec),
                                   local_data['ra'] < ra + radius / np.cos(dec)),
                    np.logical_and(local_data['dec'] > dec - radius,
                                   local_data['dec'] < dec + radius))
        print(mask.sum())
        if mask.sum() == 0:
            return None
        else:
            local_data = local_data[mask]
            c = SkyCoord(ra=ra*u.degree, dec=dec*u.degree)
            catalog = SkyCoord(ra=local_data['ra']*u.degree,
                               dec=local_data['dec']*u.degree)
            mask = catalog.separation(c) < radius * u.degree
            print(mask.sum())
            if mask.sum() == 0:
                return None
            if best:
                best = np.argmin(catalog.separation(c))
                return local_data[best]
            else:
                return local_data[mask]

    def load_data(self, catalog, ra, dec, radius):
        param = self.CATALOGS[catalog]
        coord = self._coord_search(ra, dec,
                                   param['bricks'], param['radius'],
                                   best=True)
        print('-'*40, coord)
        if coord is None:
            return '0%s' % catalog
        filename = param['brick_file'].format(*coord)
        base = self._build_basic_answer(catalog)
        print(filename, path.exists('cache/%s' % filename))
        if path.exists('cache/%s' % filename):
            result = self._coord_search(ra, dec, 'cache/%s' % filename,
                                        radius / 3600.)
            if result is None:
                # No data
                return '1%s' % catalog
            df = Table(result)
            table = html.fromstring(' '.join(df.pformat(html=True,
                                                         max_width=-1)[:-1]))
            table.attrib['border'] = '1'
            table.attrib['cellspacing'] = '0'
            base.append(table)
        else:
            with open('decam_downloads.links', 'a') as links:
                links.write('%s/%s\n' % (param['url'], filename))
            div = html.Element('div')
            div.text = 'Brick added to download list. Come back later'
            base.append(div)
        return tostring(base, method='html')
