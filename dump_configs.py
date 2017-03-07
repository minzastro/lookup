#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  1 13:59:26 2016

@author: mints
"""
#from providers.ssa import SSALookup
#from providers.wsa import WSALookup
#from providers.vsa import VSALookup
#from providers.vizier import VizierLookup
#from providers.sql import SQLLookup
#from providers.eso import ESOLookup
#from providers.sqlite import SQLiteLookup
from providers.china_vo import ChinaVOLookup
lookups = [ChinaVOLookup()]
for look in lookups:
    look.force_config_dump()
