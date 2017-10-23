# coding: utf-8
#import joblib
from glob import glob
import pickle
from lib.mocfinder import MOCFinder as MOC
mocs = {}
for name in glob('mocs/*.fits'):
    print(name)
    mocs[name[5:-5]] = MOC(name)
pickle.dump(mocs, open('all_mocs.pickle', 'wb'))
#joblib.dump(mocs, 'all_mocks.joblib')
