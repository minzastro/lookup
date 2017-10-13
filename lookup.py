# -*- coding: utf-8 -*-
"""
Created on Fri Oct 30 16:24:10 2015

@author: mints
"""
import cherrypy
from cherrypy import _cperror
from astropy.coordinates import SkyCoord
from astropy import units as u
import cPickle
from importlib import import_module
import traceback

lookups = []

for provider in ['Vizier', 'VSA', 'WSA', 'SSA', 'GCPD', 'DASCH',
                 'ESO', 'SQLite', 'ChinaVO', 'STSCI', 'CRTS2']:
    try:
        print 'Importing %s class' % provider
        class_ = getattr(import_module('providers.%s' % provider.lower()),
                         '%sLookup' % provider)
        lookups.append(class_())
    except err:
        print 'Import failed for %s' % provider
        traceback.print_tb(err.__traceback__)
        pass


def parse_arbitraty_coordinates(text):
    """
    Convert text with coordinates into ra/dec in degrees.
    Supports decimal and HMS/DMS inputs.
    """
    if '+' in text:
        ra, dec = text.split('+')
    elif '-' in text:
        ra, dec = text.split('-')
        dec = '-%s' % dec
    else:
        ra, dec = text.split(' ')
    if ('.' in ra and ' ' not in ra) or ('.' in dec and ' ' not in dec):
        return float(ra), float(dec)
    elif 'h' in ra:
        coord = SkyCoord(ra, dec)
        return coord.ra.degree, coord.dec.degree
    else:
        coord = SkyCoord(text, unit=(u.hourangle, u.deg))
        return coord.ra.degree, coord.dec.degree


def handle_error():
    cherrypy.response.status = 500
    cherrypy.response.body = [
        """<html><body><pre>Sorry, an error occured %s</pre><br>
        </body></html>""" % _cperror.format_exc()
    ]


cherrypy.config.update({'request.error_response': handle_error})


class LookupServer(object):
    def __init__(self):
        self.mocs = cPickle.load(open('all_mocs.pickle', 'r'))
        self.catalogs = {}
        for look in lookups:
            look.force_config_reload()
            for catalog in look.CATALOGS:
                print catalog, look
                self.catalogs[catalog] = look

    @cherrypy.expose
    def index(self):
        return open('index.html', 'r')

    @cherrypy.expose
    def reload_config(self):
        for look in lookups:
            look.force_config_reload()
        return """<html>Config reloaded</html>"""

    @cherrypy.expose
    def search(self, coordinates, radius):
        if float(radius) > 30:
            return """<html><body>
            <h2>Error: radius (%s) is too large</h2><br>
            <div>Maximum allowed radius is 30 arcseconds</div>
            </body></html>""" % radius
        try:
            self.ra, self.dec = parse_arbitraty_coordinates(coordinates)
            print coordinates, self.ra, self.dec
        except ValueError:
            # TODO: move to html file
            return """<html><body>Coordinates You gave cannot be interpreted.<br>
            Coordinates should be one of:
            <ul>
              <li>RA[+-\s]DE (in decimal degrees)</li>
              <li>Or any text understood by <a href="http://docs.astropy.org/en/stable/coordinates/">astropy coordinates</a></li>
            </ul>
            </body></html>
            """
        if self.dec < -90. or self.dec > 90. or self.ra < 0 or self.ra > 360.:
            return """<html><body>Coordinates You gave cannot be interpreted.<br>
            Coordinates should be one of:
            <ul>
              <li>RA[+-\s]DE (in decimal degrees)</li>
              <li>Or any text understood by <a href="http://docs.astropy.org/en/stable/coordinates/">astropy coordinates</a></li>
            </ul>
            </body></html>
            """

        catalog_list = ["'%s'" % cat for cat in self.catalogs.keys()]
        ahtml = open('results.html', 'r').readlines()
        ahtml = ' '.join(ahtml)
        ahtml = ahtml % (', '.join(catalog_list))
        self.radius = float(radius)
        return ahtml

    @cherrypy.expose
    def get_info(self, catalog):
        if catalog.lower() in self.mocs:
            if not self.mocs[catalog.lower()].is_in(self.ra, self.dec):
                # Not covered
                return '0%s' % catalog
        return self.catalogs[catalog].load_data(catalog,
                                                self.ra, self.dec,
                                                self.radius)


if __name__ == '__main__':
    cherrypy.quickstart(LookupServer(), config='lookup.conf')
