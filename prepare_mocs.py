# coding: utf-8
import joblib
from glob import glob
import cPickle
from lib.mocfinder import MOCFinder as MOC
mocs = {}
for name in glob('mocs/*.fits'):
    print name
    mocs[name[5:-5]] = MOC(name)
cPickle.dump(mocs, open('all_mocs.pickle', 'w'))
