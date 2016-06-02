# -*- coding: utf-8 -*-
"""
Created on Fri Oct 30 16:24:10 2015

@author: mints
"""
import sys
from os import path
NAME = '%s/..' % path.dirname(__file__)
sys.path.insert(0, path.abspath(NAME))
import cherrypy
from cherrypy import _cperror
import requests as rq
from lxml import html
from lxml.etree import tostring
from astropy.coordinates import SkyCoord
from astropy import units as u

VIZIER_CATALOGS = {
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

DEFAULT_RADIUS = 10.
def load_vizier(catalog, ra, dec, radius=DEFAULT_RADIUS):
    request_data = {#'-mime': 'votable',  # CSV is better, as it is compact!
                    '-source': VIZIER_CATALOGS[catalog],
                    '-out.add': '_r',
                    '-c.ra': ra,
                    '-c.dec': dec,
                    '-c.rs': radius}
    req = rq.post('http://vizier.u-strasbg.fr/viz-bin/VizieR',
                  #'http://vizier.u-strasbg.fr/viz-bin/asu-tsv',
                  data=request_data)
    text = req.text
    h = html.fromstring(text)
    r = h.xpath('//div[@id="CDScore"]/table[@class="sort"]')
    if len(r) == 0:
        return ''
    r = r[0]
    for element in r.xpath('//a[@class="full"]'):
        element.attrib['href'] = 'http://vizier.u-strasbg.fr/viz-bin/' + element.attrib['href']
    base = html.Element('div')
    header = html.Element('h2')
    header.text = catalog
    base.append(header)
    base.append(r)
    return tostring(base)

def _get_mags(maglist, prefix='PetroMag'):
    out = ['{0}{1},{0}{1}Err'.format(m, prefix) for m in maglist]
    return ','.join(out)

VSA_CATALOGS = {'VHS': ('VHSDR3', 'VHSsource',
                        'sourceID,ra,dec,mergedClass,pStar,eBV,' +
                        _get_mags(['y', 'j', 'h', 'ks'])),
'VIKING': ('VIKINGDR4', 'vikingSource',
                        'sourceID,ra,dec,mergedClass,pStar,eBV,' +
                        _get_mags(['z', 'y', 'j', 'h', 'ks'])),
'VVV': ('VVVDR4', 'vvvSource',
                        'sourceID,ra,dec,mergedClass,pStar,' +
                        _get_mags(['z', 'y', 'j', 'h', 'ks'], 'AperMag3')),
}

def load_vsa(catalog, ra, dec, radius=DEFAULT_RADIUS):
    url = "http://horus.roe.ac.uk:8080/vdfs/WSASQL"
    #prepared_url = url % query
    param = VSA_CATALOGS[catalog]
    payload = {'database': param[0],
               'archive': 'VSA',
               'formaction': 'region',
               'from': param[1],
               'ra': ra,
               'dec': dec,
               'sys': 'J',
               'xSize':'',
               'ySize':'',
               'name': '',
               'radius': radius/60.,
               'boxAlignment': 'RADec',
               'emailAddress': '',
               'format': 'HTML',
               'compress': 'GZIP',
               'rows': '5',
               'select': param[2],
               }
    req = rq.get(url, params=payload)
    text = req.content
    print text
    h = html.fromstring(text)
    r = h.xpath('//table[count(tr)>1]')
    if len(r) == 0:
        return ''
    r = r[0]
    base = html.Element('div')
    header = html.Element('h2')
    header.text = catalog
    base.append(header)
    base.append(r)
    return tostring(base)


def parse_arbitraty_coordinates(text):
    if '+' in text:
        ra, dec = text.split('+')
    elif '-' in text:
        ra, dec = text.split('-')
        dec = '-%s' % dec
    else:
        ra, dec = text.split(' ')
    if ('.' in ra and not ' ' in ra) or ('.' in dec and not ' ' in dec):
        return float(ra), float(dec)
    elif 'h' in ra:
        coord = SkyCoord(ra, dec)
        return coord.ra.degree, coord.dec.degree
    else:
        coord = SkyCoord(text, unit=(u.hourangle, u.deg))
        return coord.ra.degree, coord.dec.degree


LOCAL = '127.0.0.1:8001'
SESSION_KEY = '_cp_username'

def error_page_404(status, message, traceback, version):
    return "Error %s - Page does not exist yet. It might appear later!" % status

def handle_error():
    cherrypy.response.status = 500
    cherrypy.response.body = [
        """<html><body><pre>Sorry, an error occured %s</pre><br>
        <a href="mailto:arches.support@astro.unistra.fr" target="_top">Contact ARCHES support team (please refer to ICF in the mail subject)</a><br>
        </body></html>""" % _cperror.format_exc()
    ]

cherrypy.config.update({'error_page.404': error_page_404,
                        'request.error_response': handle_error})

class LookupServer(object):
    @cherrypy.expose
    def index(self):
        return open('index.html', 'r')

    @cherrypy.expose
    def search(self, coordinates):
        self.ra, self.dec = parse_arbitraty_coordinates(coordinates)
        catalog_list = VIZIER_CATALOGS.keys() + VSA_CATALOGS.keys()
        catalog_list = ["'%s'" % cat for cat in catalog_list]
        ahtml = open('results.html', 'r').readlines()
        ahtml = ' '.join(ahtml)
        ahtml = ahtml % (', '.join(catalog_list))
        return ahtml


    @cherrypy.expose
    def get_info(self, catalog):
        if catalog in VIZIER_CATALOGS:
            return load_vizier(catalog, self.ra, self.dec)
        elif catalog in VSA_CATALOGS:
            return load_vsa(catalog, self.ra, self.dec)


if __name__ == '__main__':
    cherrypy.quickstart(LookupServer(), config='lookup.conf')

