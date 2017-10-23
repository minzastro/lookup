#!/usr/bin/python
import healpy
import numpy as np
from astropy.io import fits


def uniq(value):
    """
    Convert from NUNIQ HEALPix coding method used for MOCs into
    order-index pairs.
    See http://www.ivoa.net/documents/MOC/20130910/WD-MOC-1.0-20130910.html
    for details.
    """
    order = int(np.log2(value/4)/2)
    npix = value - 4 * (4**order)
    return order, npix


def cell_area(level):
    return (129600. / np.pi) * 4**(-level) / 12.


class MOCFinder(object):
    """
    Class to search for positions in HEALPix Multi-Order Coverage maps.
    See http://www.ivoa.net/documents/MOC/20130910/WD-MOC-1.0-20130910.html
    MOCs can be prepared with Aladin or stilts or downloaded from
    http://alasky.u-strasbg.fr/footprints/tables/vizier/
    """
    def __init__(self, filename):
        """
        filename - FITS file containing MOC map.
        """
        fitstbl = fits.open(filename)[1]
        self.healpix = {}
        for row in fitstbl.data:
            order, npix = uniq(row[0])
            if order not in self.healpix:
                self.healpix[order] = []
            self.healpix[order].append(npix)

    def is_in(self, ra, decl):
        """
        Check if position is in the MOC map.
        ra, decl - sky coordinates.
        TODO: implement vectorized ra/decl support.
        """
        ra = np.atleast_1d(ra)
        decl = np.atleast_1d(decl)
        theta = 0.5*np.pi - np.radians(decl)
        phi = np.radians(ra)
        keys = list(self.healpix.keys())
        keys.sort()
        todo = np.ones(len(ra), dtype=bool)
        fullmask = np.arange(len(ra), dtype=int)
        for level in keys:
            healpix_cell = healpy.ang2pix(2**level, theta[todo], phi[todo],
                                          nest=True)
            mask = np.copy(fullmask[todo])
            for icell, cell in enumerate(healpix_cell):
                if cell in self.healpix[level]:
                    try:
                        todo[mask[icell]] = False
                    except IndexError:
                        import ipdb; ipdb.set_trace()
        return ~todo

    def get_area(self):
        area = 0.
        for level in self.healpix.keys():
            area = area + cell_area(level) * len(self.healpix[level])
        return area

if __name__ == '__main__':
    moc_finder = MOCFinder('../rs/moc/MOC_sdss.fits')
    print(moc_finder.is_in([270., 140., 272., 0.], [24., -80, 22., -75.]))
