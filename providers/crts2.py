from providers.multipart import MultipartLookup
from lxml import html


class CRTS2Lookup(MultipartLookup):

    URL = "http://nunuku.caltech.edu/cgi-bin/getcssconedb_release_img.cgi"

    XPATH = '//div[contains(@class, "tabbertab")]/table//table'

    def force_config_reload(self):
        self.CATALOGS = {'CRTS2': ''}

    def _prepare_request_data(self, catalog, ra, dec, radius):
        radius = float(radius) / 60.
        payload = {'IMG': 'nun',
                   'OUT': 'csv',
                   'SHORT': 'short',
                   'DB': 'photcat',
                   'RA': str(ra),
                   'Dec': str(dec),
                   'Rad': str(radius),
                   '.submit': 'Submit',
                   'PLOT': 'plot'}
        return payload

    def _post_process_table(self, table):
        for element in table.xpath('//a'):
            if element.attrib['href'].startswith('#'):
                element.attrib['href'] = self.URL + element.attrib['href']
            element.attrib['target'] = '_blank'
        table.attrib['bgcolor'] = ''
        div = html.Element('div')
        div.append(table)
        div.append(self.result_html.xpath('//font/a[contains(text(), "download")]')[0])
        return div
