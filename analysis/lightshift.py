import numpy as np
import scipy as sp

from constants import *


def acstark(w_laser, power, waist, atom):
    """The ac Stark shift, without the rotating wave approximation.

    **Inputs**

      * w_laser: float, laser wavelength in meters
      * power: float, laser power in Watts
      * waist: float, waist size (i.e. 1/e^2 radius) of the laser beam in meters
      * atom: Atom instance, see atoms.py

    **Outputs**

      * acshift: float, the ac Stark shift

    **Notes**

    The detuning is so large that the rotating wave approximation is invalid.

    """

    lw = atom.linewidth
    omega_l = c0/w_laser * 2*np.pi
    omega0 = c0/atom.wavelength * 2*np.pi
    intensity = 2*power/(np.pi*waist**2)
    acshift = 3*np.pi*c0**2/(2*omega0**3) * (lw/(omega0-omega_l)+\
                                             lw/(omega0+omega_l)) * intensity

    return acshift


def recoil_energy(wavelength, mass):
    """Recoil energy for a given wavelength in meters.

    The recoil energy is defined as :math:`Er=\hbar^2k^2/2m`, with
    :math:`k=2\pi/\lambda` the wavevector for the light and m the atomic mass.

    """

    return 2*hbar**2*np.pi**2/(mass*wavelength**2)


def trapfreqs(U0, waist, mass, w_laser):
    """Trap frequencies for a single beam ODT

    **Inputs**

      * U0: float, trap depth of the ODT in Joules
      * waist: float, waist (1/e^2 radius) of the beam in meters
      * mass: float, mass of the atom
      * w_laser: float, laser wavelength in meters

    **Outputs**

      * wr: float, radial trap frequency in rad/s
      * wz: float, axial trap frequency in rad/s

    """

    zR = np.pi*waist**2/w_laser
    wr = np.sqrt(4*U0/(mass*waist**2))
    wz = np.sqrt(2*U0/(mass*zR**2))

    return wr, wz


def saturation_intensity(w_atom, linewidth):
    """The saturation intensity

    **Inputs**

      * w_atom: float, resonant wavelength for the atom. For very large
                detuning, this is the middle between the D1 and D2 lines.
      * linewidth: float, linewidth for the atomic transition (usually the one
                   for the D2 line if an alkali atom) in rad/s

    **Outputs**

      * Isat: float, the saturation intensity in W/m^2

    """

    lw = linewidth
    Isat = (np.pi*h*c0*lw) / (3*w_atom**3)

    return Isat


def scrate_fardetuned(w_laser, power, waist, atom):
    """Scattering rate per atom for far-detuned light

    Far-resonant means that the rotating wave approximation is not made. The
    assumption that is made is that the population of the excited state of the
    atom is negligible.

    **Inputs**

      * w_laser: float, laser wavelength in meters
      * power: float, laser power in Watts
      * waist: float, waist size (i.e. 1/e^2 radius) of the laser beam in meters
      * atom: Atom instance, see atoms.py

    **Outputs**

      * scrate: float, the scattering rate in Hz

    **References**

    R. Grimm and M. Weidemuller, _Optical dipole traps for neutral atoms_,
    arXiv:physics/9902072 (1999).

    """

    omega_l = c0/w_laser * 2*np.pi
    omega0 = c0/atom.wavelength * 2*np.pi
    intensity = 2*power/(np.pi*waist**2)
    lw = atom.linewidth
    scrate = 3*np.pi*c0**2/(2*hbar*omega0**3) * (omega_l/omega0)**3 * \
                 (lw/(omega0-omega_l) + lw/(omega0+omega_l))**2 * intensity

    return scrate


def scrate_neardetuned(atom, power, waist, detuning):
    """Scattering rate per atom for near-resonant light

    Near-resonant means that the rotating wave approximation is made. The
    expression is based on the optical Bloch equations, so saturation of the
    upper state of the two-level atom is taken into account.

    **Inputs**

      * atom: Atom instance, see atoms.py
      * power: float, laser power in Watts
      * waist: float, waist size (i.e. 1/e^2 radius) of the laser beam in meters
      * detuning: float, detuning in rad/s

    **Outputs**

      * scrate: float, the scattering rate in Hz

    **References**

    Metcalf and Van der Straten, Laser Cooling and Trapping (1997).

    """

    intensity = 2*power/(np.pi*waist**2)
    s0 = intensity / atom.sat_intensity()

    scrate = (s0 * atom.linewidth/2) / (1 + s0 + (2*detuning/atom.linewidth)**2)

    return scrate
