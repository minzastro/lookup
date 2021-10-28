import cherrypy
from cherrypy import _cperror
from cherrypy import log as cherrylog
from cherrypy.lib.reprconf import Config
from astropy.coordinates import SkyCoord
from astropy import units as u
import pickle
from importlib import import_module
import traceback
from lxml import html
from lxml.etree import tostring
import jinja2


class LookupServer(object):
    def __init__(self):
        self.mocs = pickle.load(open('all_mocs.pickle', 'rb'))
        self.catalogs = {}
        self.config = Config('lookup.conf')
        #for look in lookups:
        #    look.force_config_reload()
        #   for catalog in look.CATALOGS:
        #        print(catalog, look)
        #        self.catalogs[catalog] = look

    def start(self):
        cherrypy.config.update(self.config)
        cherrypy.tree.mount(self, '/', config=self.config)
        cherrypy.tree.mount(self, '/lookup', config=self.config)
        cherrypy.engine.start()
        cherrypy.engine.block()

    @cherrypy.expose
    def index(self):
        return open('index.html', 'r')

    @cherrypy.expose
    def search(self, coordinates, radius):
        not_in = ['SDSS', 'Gaia', 'Hoho']
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
                       document.getElementById("header-"+name).innerHTML = " click to expand";
                       document.getElementById("result-"+name).innerHTML = response;
                   }
                   else if (jX.status == 204){
                       document.getElementById("over-"+name).remove();
                   }
               }
               );
           }
           jQuery(window).load(function(){
               var catalogs = {{catalogs}};
               var counter = catalogs.length;
               for (var i = 0; i < catalogs.length; i++) {
                  askCatalog(catalogs[i]);
               }
            });
        </script>
        </head>
        <body>
        <h2> not in {{ ','.join(not_in)}}</h2>
        {% for catalog in catalogs %}
           <details id="over-{{catalog}}">
             <summary>
               <h2 class="head"> {{ catalog }}</h2> <div  class="head" id="header-{{catalog}}">...pending</div>
            </summary>
            <div id="result-{{catalog}}">{{ catalog }}</div>
           </details>
        {% endfor %}
        </body>
        </html>
        """)
        return main_template.render(not_in=not_in, catalogs=list(self.mocs.keys()))

    @cherrypy.expose
    def get_info(self, catalog):
        if catalog == 'sdss':
            cherrypy.response.status = 200
        else:
            cherrypy.response.status = 204
        return "%s result table" % catalog


if __name__ == '__main__':
    server = LookupServer()
    server.start()
