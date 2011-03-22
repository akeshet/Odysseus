"""The `atoms` module defines physical properties of atoms.

The base class Atom() specifies the properties that need to be filled in
for each particular atom, and functions to calculate properties like the
saturation intensity and recoil energy. It is meant to only be subclassed,
not used directly.

"""


import os
import imp

import numpy as np

from constants import h, hbar, c0, mp


class Atom(object):
    """Base class, not used directly. Defines a common interface."""

    name = None
    wavelength = None
    linewidth = None
    mass = None


    def resonantfreq(self):
        """Frequency in Hz as determined from the resonant wavelength."""

        return c0/self.wavelength


    def sat_intensity(self):
        """The saturation intensity.

        **Outputs**

          * Isat: float, the saturation intensity in W/m^2

        """

        Isat = (np.pi*h*c0*self.linewidth) / (3*self.wavelength**3)
        return Isat


    def sclength(self, bfield=0):
        """The scattering length as a function of magnetic field."""

        return 0


    def Er(self):
        """Recoil energy for resonant wavelength of the atom."""

        return 2*hbar**2*np.pi**2/(self.mass*self.wavelength**2)


    def recoilfreq(self):
        """Recoil frequency in rad/s"""

        return self.Er()/hbar


class Li6(Atom):
    """Properties of Lithium-6."""

    name = 'Lithium 6'
    mass = 6*mp
    wavelength = 670.979e-9
    linewidth = 2*np.pi*5.92e6

    def __init__(self, state='12'):
        """State is one of ('12', '13', '23')"""

        self.state = state

        odysspath = imp.find_module('odysseus')[1]
        datapath = os.path.join(odysspath, 'analysis', 'datafiles')
        self.a12 = np.load(os.path.join(datapath, 'LiFeshbach_12.npy'))
        self.a13 = np.load(os.path.join(datapath, 'LiFeshbach_13.npy'))
        self.a23 = np.load(os.path.join(datapath, 'LiFeshbach_23.npy'))


    def sclength_12(self, bfield):
        """Return scattering length between states |1> and |2> for given B."""
        return np.interp(bfield, self.a12[:, 0], self.a12[:, 1])


    def sclength_13(self, bfield):
        """Return scattering length between states |1> and |3> for given B."""
        return np.interp(bfield, self.a13[:, 0], self.a13[:, 1])


    def sclength_23(self, bfield):
        """Return scattering length between states |2> and |3> for given B."""
        return np.interp(bfield, self.a23[:, 0], self.a23[:, 1])


    def sclength(self, bfield=0):
        """Scattering length for given B-field. Depends on the two states."""

        sclen_states = {'12':self.sclength_12, '13':self.sclength_13,
                        '23':self.sclength_23}
        return sclen_states[self.state](bfield)


class K40(Atom):
    """Properties of Potassium-40."""

    name = 'Potassium 40'
    wavelength = 766.7e-9
    linewidth = 2*np.pi*6.09e6
    mass = 40*mp


class Rb85(Atom):
    """Properties of Rubidium-85.

    Note that this is only the D2 line. For more accurate results the D1 line
    needs to be taken into account as well.
    """

    name = 'Rubidium 85'
    wavelength = 780.24e-9
    linewidth = 2*np.pi*5.98e6
    mass = 85*mp


class Cs(Atom):
    """Properties of Cesium-133.

    Note that this is only the D2 line. For more accurate results the D1 line
    needs to be taken into account as well.
    """

    name = 'Cesium'
    wavelength = 852.35e-9
    linewidth = 2*np.pi*5.18e6
    mass = 133*mp


class Na(Atom):
    """Properties of Sodium-23"""

    name = 'Sodium'
    wavelength = 589.162e-9
    linewidth = 2*np.pi*9.80e6
    mass = 23*mp