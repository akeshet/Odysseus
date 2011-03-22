from nose import SkipTest

from odysseus.fitfermions import find_ellipticity
from odysseus.refimages import generate_image, stretch_img


class TestNormAndGuess:
    def test_norm_and_guess(self):
        raise SkipTest # TODO: implement your test here


class TestFindEllipticity:
    def setup(self):
        self.ellip = 0.81
        self.img = generate_image()
        stretch_img(self.img, 1/self.ellip)

    def test_find_ellipticity(self):
        tol = 2e-3
        assert find_ellipticity(self.img, tol=tol) - self.ellip < tol


class TestDoFit:
    def test_do_fit(self):
        raise SkipTest # TODO: implement your test here


class TestFitImg:
    def test_fit_img(self):
        raise SkipTest # TODO: implement your test here

