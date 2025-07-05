import cherrypy
from cherrypy import log as cherrylog
from cherrypy.lib.reprconf import Config
from astropy.coordinates import SkyCoord
from astropy import units as u
import pickle
from importlib import import_module
import traceback
import jinja2

lookups = []

for provider in ['ObsLog',
                 'Q3CTap', 'BoxTap',
                 'Vizier', 'VSA', 'WSA',
                 'GCPD',
                 'DASCH', 'OGLE',
                 'ESO', 'ChinaVO', 'STSCI', 'CRTS2',
                 #'DECam',
                 'CasJobs'
                 ]:
    try:
        print('Importing %s class' % provider)
        print('providers.%s' % provider.lower(), '%sLookup' % provider)
        class_ = getattr(import_module('providers.%s' % provider.lower()),
                         '%sLookup' % provider)
        lookups.append(class_())
    except Exception as err:
        print('Import failed for %s' % provider)
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


class LookupServer(object):
    def __init__(self):
        self.mocs = pickle.load(open('all_mocs.pickle', 'rb'))
        self.catalogs = {}
        self.config = Config('lookup.conf')
        for look in lookups:
            look.force_config_reload()
            for catalog in look.CATALOGS:
                print(catalog, look)
                self.catalogs[catalog] = look

    def start(self):
        cherrypy.config.update(self.config)
        cherrypy.tree.mount(self, '/', config=self.config)
        cherrypy.tree.mount(self, '/lookup', config=self.config)
        cherrypy.engine.start()
        cherrypy.engine.block()

    @cherrypy.expose
    def index(self):
        return open('index.html', 'r')


#$('#alphBnt').on('click', function(){
#    var alphabeticallyOrderedDivs = $divs.sort(function(a,b){
#        return $(a).find("h1").text() > $(b).find("h1").text();
#    });
#    $("#container").html(alphabeticallyOrderedDivs);
#});
    @cherrypy.expose
    def search(self, coordinates, radius):
        self.ra, self.dec = parse_arbitraty_coordinates(coordinates)
        self.radius = float(radius)

        main_template = jinja2.Template("""
        <html>
        <head>
        <link rel="stylesheet" type="text/css" href="static/lookup.css">
        <script type="text/javascript" charset="utf8" src="static/jquery.js"></script>
        <script type="text/javascript" language="javascript" class="init">
           function askCatalog(name){
               var params = {catalog: name};
               jQuery.post('get_info', params,
               function(response, textStatus, jX){
                   if (jX.status == 200){
                       document.getElementById("header-"+name).innerHTML = " click to collapse";
                       document.getElementById("result-"+name).innerHTML = response;
                       document.getElementById("over-"+name).toggleAttribute('open');
                   }
                   else if (jX.status == 205){
                       document.getElementById("over-"+name).remove();
                       document.getElementById("notcovered").innerHTML += " " + name;
                   }
                   else if (jX.status == 204){
                       document.getElementById("over-"+name).remove();
                       document.getElementById("nodata").innerHTML += " " + name;
                   }
                   else if (jX.status == 203){
                       document.getElementById("over-"+name).remove();
                       document.getElementById("errors").innerHTML += " " + name;
                   }
               }
               );
           }
           jQuery(window).on('load', function(){
               var catalogs = {{catalogs}};
               var counter = catalogs.length;
               for (var i = 0; i < catalogs.length; i++) {
                  askCatalog(catalogs[i]);
               }
            });
        </script>
        </head>
        <body>
        <h1>Search around: {{ra}} {{dec}}</h1>
        {% for catalog in catalogs %}
           <details id="over-{{catalog}}">
             <summary>
               <h2 class="head"> {{ catalog }}</h2> <div  class="head" id="header-{{catalog}}">...pending</div>
            </summary>
            <div id="result-{{catalog}}">{{ catalog }}</div>
           </details>
        {% endfor %}
        <div id="notcovered">Not covered by:</div>
        <div id="nodata">No data from:</div>
        <div id="errors">Error from:</div>
        </body>
        </html>
        """)
        return main_template.render(catalogs=list(self.catalogs.keys()),
                                    ra=self.ra,
                                    dec=self.dec)

    @cherrypy.expose
    def get_info(self, catalog):
        if catalog.lower() in self.mocs:
            if not self.mocs[catalog.lower()].is_in(self.ra, self.dec):
                # Not covered
                cherrypy.response.status = 205
                return ""
        try:
            print(catalog, self.ra, self.dec, self.radius)
            result = self.catalogs[catalog].load_data(catalog,
                                                      self.ra, self.dec,
                                                      self.radius)
            cherrypy.response.status = result['status']
            print(catalog, result['status'])
            return result['html']
        except Exception as exc:
            cherrylog.error('Error for catalog: %s' % catalog)
            cherrylog.error(str(exc))
            cherrylog.error(traceback.format_exc())
            cherrypy.response.status = 203
            return ""



if __name__ == '__main__':
    server = LookupServer()
    server.start()
