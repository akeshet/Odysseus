from nose import SkipTest
from nose.tools import assert_raises
import numpy as np
from numpy.testing import assert_approx_equal, assert_array_almost_equal, \
     assert_array_equal

from odysseus import imageprocess


class TestTrans2od:
    def test_trans2od(self):
        raise SkipTest # TODO: implement your test here

class TestOd2trans:
    def test_od2trans(self):
        raise SkipTest # TODO: implement your test here

class TestCalcAbsimage:
    def test_calc_absimage(self):
        raise SkipTest # TODO: implement your test here

class TestThresholdImage:
    def test_threshold_image(self):
        raise SkipTest # TODO: implement your test here


class TestFindFitrange:
    def test_find_fitrange_withcut(self):
        testprof= np.arange(4, 0, -0.1)
        cutoff = imageprocess.find_fitrange(testprof)
        assert cutoff==30

    def test_find_fitrange_nocut(self):
        testprof= np.arange(1, 0, -0.01)
        cutoff = imageprocess.find_fitrange(testprof, od_max=1.01, min_cutoff=3)
        assert cutoff==3

    def test_find_fitrange_shortinput(self):
        testprof = np.arange(5)
        assert_raises(ValueError, imageprocess.find_fitrange, testprof)


class TestRadialInterpolate:
    def test_radial_interpolate(self):
        raise SkipTest # TODO: implement your test here

class TestLineprofiles:
    def test_lineprofiles(self):
        raise SkipTest # TODO: implement your test here

class TestRadialprofileErrors:
    def test_radialprofile_errors(self):
        raise SkipTest # TODO: implement your test here

class TestBilinearInterpolate:
    def test_bilinear_interpolate(self):
        raise SkipTest # TODO: implement your test here

class TestImgslice:
    def test_imgslice(self):
        raise SkipTest # TODO: implement your test here


class TestMirrorLine:
    def test_mirror_line(self):
        coord = np.arange(3) + 1
        mir_coord = imageprocess.mirror_line(coord)
        assert_array_equal(mir_coord, np.array([3., 2.,  1.,  2.,  3.]))

    def test_mirror_line_neg(self):
        coord = np.arange(3)
        mir_coord = imageprocess.mirror_line(coord, negative_mirror=True)
        assert_array_equal(mir_coord, np.array([-2., -1.,  0.,  1.,  2.]))


class TestSmooth:
    def test_smooth(self):
        raise SkipTest # TODO: implement your test here

class TestMaxodCorrect:
    def test_maxod_correct(self):
        raise SkipTest # TODO: implement your test here

class TestNormalizeImg:
    def test_normalize_img(self):
        raise SkipTest # TODO: implement your test here


class TestNormalizeEdgestrip:
    def test_normalize_edgestrip(self):
        eyecenter = imageprocess.normalize_edgestrip(np.eye(3), normval=1/3.,
                                                     striplen=1)[1,1]
        assert_approx_equal(eyecenter, 1)
