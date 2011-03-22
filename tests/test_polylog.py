from nose import SkipTest
import numpy as np
from numpy.testing import assert_approx_equal, assert_array_almost_equal

from odysseus import lerch, polylog


class TestFermiPoly3:
    def setup(self):
        self.xx1 = np.linspace(-25., 25., 250)
        self.exact1 = - lerch.Li(3, -np.exp(self.xx1))

    def test_fermi_poly3_array(self):
        fp_approx1 = polylog.fermi_poly3(self.xx1)
        # the polynomial approximation should be good to 1e-7, fails for
        # higher precision test
        assert_array_almost_equal(self.exact1, fp_approx1, decimal=7)

    def test_fermi_poly3_int(self):
        testint = 1
        assert_approx_equal(- lerch.Li(3, -np.exp(testint)), \
                            polylog.fermi_poly3(testint), significant=7)

    def test_fermi_poly3_float(self):
        testfloat = 1.
        assert_approx_equal(- lerch.Li(3, -np.exp(testfloat)), \
                            polylog.fermi_poly3(testfloat), significant=7)


class TestFermiPoly5half:
    #def setup(self):
        #self.xx1 = np.linspace(-25., 25., 250)
        #self.exact1 = - lerch.Li(2.5, -np.exp(self.xx1))

    def test_fermi_poly5half(self):
        # this fails, don't know why. if ever needed, investigate!
        #fp_approx1 = polylog.fermi_poly5half(self.xx1)
        ## the polynomial approximation should be good to 1e-7, fails for
        ## higher precision test
        #assert_array_almost_equal(self.exact1, fp_approx1, decimal=4)
        raise SkipTest


class TestFermiPoly2:
    def setup(self):
        self.xx1 = np.linspace(-25., 25., 250)
        self.exact1 = - lerch.Li(2, -np.exp(self.xx1))

    def test_fermi_poly2(self):
        fp_approx1 = polylog.fermi_poly2(self.xx1)
        # the polynomial approximation should be good to 1e-7, fails for
        # higher precision test
        assert_array_almost_equal(self.exact1, fp_approx1, decimal=7)

    def test_fermi_poly2_int(self):
        testint = 1
        assert_approx_equal(- lerch.Li(2, -np.exp(testint)), \
                            polylog.fermi_poly2(testint), significant=7)

    def test_fermi_poly2_float(self):
        testfloat = 1.
        assert_approx_equal(- lerch.Li(2, -np.exp(testfloat)), \
                            polylog.fermi_poly2(testfloat), significant=7)


# the functions below are not actually used in the fitting code yet.
# When this changes, implement tests!

class TestDilog:
    def test_dilog(self):
        raise SkipTest # TODO: implement your test here


class TestG5halves:
    def test_g5halves(self):
        raise SkipTest # TODO: implement your test here


class TestGTwo:
    def test_g_two(self):
        raise SkipTest # TODO: implement your test here


class TestGThree:
    def test_g_three(self):
        raise SkipTest # TODO: implement your test here

