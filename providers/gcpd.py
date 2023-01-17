from providers.basic import BasicLookup
from astropy.coordinates import SkyCoord
from astropy import units as u
from copy import deepcopy
from lxml.etree import tostring
from lxml import html

class GCPDLookup(BasicLookup):

    URL = "http://obswww.unige.ch/gcpd/cgi-bin/genIndex.cgi"

    DEBUG = False

    def force_config_reload(self):
        self.CATALOGS = {'GCPD': ''}

    def _prepare_request_data(self, catalog, ra, dec, radius):
        coord = SkyCoord(ra, dec, unit='deg')
        ra0 = coord.ra.to_string(unit=u.hour, sep=' ', precision=0)
        dec_tuple = coord.dec.dms
        if dec > 0:
            dec0 = '%d %.2d' % (int(dec_tuple[0]),
                                dec_tuple[1] + float(dec_tuple[2]) / 60.)
        else:
            dec0 = '-%d %.2d' % (abs(int(dec_tuple[0])),
                                abs(dec_tuple[1] + float(dec_tuple[2]) / 60.))

        radius = float(radius) / 60.
        print(ra, dec, ra0, dec0, dec_tuple)

        payload = {'ident': '',
                   'equin': '2000',
                   'ra': ra0,
                   'dec': dec0,
                   'ras': radius,
                   'decs': radius,
                   'button': 'Query by Coordinates'}
        return payload

    def load_data(self, catalog, ra, dec, radius):
        """
        Load data, extract html table and prepare output div.
        """
        h = self._get_html_data(catalog, ra, dec, radius)
        base = self._build_basic_answer(catalog)
        r = h.xpath('//h2')
        if len(r) < 2:
            # No data
            return {'status': 204, 'html': 'No data'}
        for h2 in r[1:]:
            div = html.Element('div')
            next_element = h2.getnext()
            hnew = deepcopy(h2)
            hnew.tag = 'h3'
            div.append(hnew)
            if next_element is None:
                continue
            while next_element is not None and next_element.tag != 'table':
                div.append(deepcopy(next_element))
                next_element = next_element.getnext()
            div.append(deepcopy(self._post_process_table(next_element)))
            base.append(deepcopy(div))
        return {'status': 200, 'html': tostring(base, method='html')}

    def _post_process_table(self, table):
        """
        First column contains references to full record on vizier - need
        to correct the URL there.
        """
        for element in table.xpath('//a'):
            element.attrib['href'] = 'http://obswww.unige.ch' + \
                                     element.attrib['href']
            element.attrib['target'] = '_blank'
        return table
