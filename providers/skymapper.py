from providers.basic import BasicLookup
from astropy.io import votable
from lxml import html


class SkyMapperLookup(BasicLookup):
    """
    Provider for SkyMapper data.
    """
    CATALOGS = {'SkyMapper': None}

    URL = 'http://skymapper.anu.edu.au/sm-cone/query'

    XPATH = '//table'

    def _prepare_request_data(self, catalog, ra, dec, radius):
        return {'RA': ra,
                'DEC': dec,
                'SR': radius / 3600.,
                'VERB': 1}
        
    def _post_process_table(self, table):
        children = table.getchildren()
        thead = html.Element('thead')
        theadrow = html.Element('tr')
        for child in children[:-1]:
            element = html.Element('th')
            element.text = child.attrib['name']
            theadrow.append(element)
        thead.append(theadrow)
        new_table = html.Element('table')
        new_table.attrib['border'] = '1'
        new_table.attrib['cellspacing'] = '0'
        new_table.append(thead)
        new_table.append(children[-1].getchildren()[0])
        return new_table
