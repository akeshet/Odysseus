from nose import SkipTest
import numpy as np
from numpy.testing import assert_array_almost_equal

from odysseus.centerofmass import center_of_mass


class TestCenterOfMass:
    def setUp(self):
        self.ones = np.ones((101, 101))
        self.ones[50, 50] = 2

    def test_center_of_mass(self):
        com_ones = center_of_mass(self.ones)
        assert_array_almost_equal(com_ones, (50, 50), decimal=1)

