"""Optical lattice structure and energies.

The purpose of this module is to calculate the band structure of a 1D optical
lattice, give typical energy scales of an atom in a lattice and visualize the
band structure.

Energies are typically expressed in recoil energies. The recoil energy is
defined as :math:`Er=\hbar^2k^2/2m` (see `lightshift`), with k the
wavevector of the laser light that creates the lattice. Note that in
some articles k is defined as the reciprocal lattice vector, this will give
an error of a factor of 4 in all energies.

"""


import numpy as np
import scipy as sp
import matplotlib.pyplot as plt


def bandstructure(U0, jmax=10, numq=100):
    """Calculate the band energies for a 1D lattice with depth U0.

    Got expressions from the thesis of Daley (2005). Greiner (2003) gives
    the same expressions with the exception of the U0/2 term on the diagonal
    of the Hamiltonian. This term is needed to keep the bottom of the band at
    zero energy.

    **Inputs**

      * U0: scalar, the lattice depth in recoils
      * jmax: int, the maximum l considered (see Daley thesis, p.17)
      * numq: int, the number of positive quasi-momenta for which the
              band energies are calculated

    **Outputs**

      * band_energies: 2D array, containing the eigen energies in recoils for
                       several bands and a range (numq values) of quasi momenta
                       equally distributed from zero to the band edge.
      * blochstate_coeffs: 3D array, containing the coefficients
                           :math:`c_J^{(n,q)}` of the Fourier expansion of
                           the Bloch functions of the lattice.

    **References**

    A. J. Daley, Manipulation and Simulation of Cold Atoms in Optical Lattices,
    Innsbruck (2005).

    """

    quasi_k = np.linspace(0, 1, num=numq)
    band_energies = np.zeros((2*jmax+1, numq))
    blochstate_coeffs = np.zeros((2*jmax+1, 2*jmax+1, numq))

    for ii, qk in enumerate(quasi_k):
        # construct the Hamiltonian
        # diagonal terms given by free-space dispersion relations
        v_kin = (np.arange(-jmax, jmax+1)*2 + qk)**2 + U0/2.
        # off-diagonal terms given by the cosine potential
        v_hop = -np.ones(2*jmax)*U0/4.
        ham = np.diag(v_hop, 1) + np.diag(v_hop, -1) + np.diag(v_kin, 0)

        energy_ii, blochstate = np.linalg.eig(ham)
        energy_ii.sort()
        band_energies[:, ii] = energy_ii
        blochstate_coeffs[:, :, ii] = blochstate

    return band_energies, blochstate_coeffs


def latt_energies(U0, printing=False):
    """Calculate the band structure, gap, width and tunneling element.

    The results are for a 1D lattice. For a 3D cubic lattice the bandwidth is
    three times larger, the tunneling matrix element (tJ) stays the same.
    tJ is given by bandwidth/(4D), with D the lattice dimension, as described
    on p.91 of the thesis of D. Jaksch.

    **Inputs**

      * U0: scalar, the lattice depth in recoil energies
      * printing, bool, if True print the results for band width, gap and tJ.

    **Outputs**

      * band_energies: 2D array, containing the eigen energies in recoils for
                       several bands and a range (numq values) of quasi momenta
                       equally distributed from zero to the band edge.
      * bandwidth: float, the band width in recoils
      * bandgap: float, the band gap in recoils
      * tJ: float, the tunneling matrix element in recoils.

    """

    bandenergies, blochstates = bandstructure(U0)
    bandwidth = bandenergies[0, :].max() - bandenergies[0, :].min()
    bandgap = bandenergies[1, :].min() - bandenergies[0, :].max()
    tJ = bandwidth/4

    if printing:
        print 'bandwidth = ', bandwidth
        print 'bandgap = ', bandgap
        print 'J = ', tJ

    return bandenergies, bandwidth, bandgap, tJ


def Etrap(N, a_lat, mass, wr, wz=None):
    """Return the energy scale of harmonic confinement in the (3D) lattice

    **Inputs**

      * N: int, number of atoms
      * a_lat: float, the lattice constant in meters
      * mass: float, the mass of the atom
      * wr: float, radial trap frequency in rad/s
      * wz: float, axial trap freq. If None it is assumed equal to `wr`.

    **Outputs**

      * Et: float, the typical energy scale of the harmonic confinement

    **References**

    Schneider et al., Science 322, 1520 (2008).

    """

    if not wz:
        wz = wr
    Vt = 0.5*mass*wr**2*a_lat**2
    Et = Vt * (wr/wz * N * 3/(4*np.pi))**(2./3)

    return Et


def plot_bands(bstruct, nbands=3, foldover=True):
    """Show the band structure for a given number of bands

    **Inputs**

      * bstruct: 2D array, band structure of a 1D lattice as obtained from the
                 bandstructure() function.
      * nbands: int, the number of bands that is plotted
      * foldover: bool, if True `bstruct` is folded over so the plot covers all
                  quasi-momenta instead of those from 0 to the band edge.

    **Outputs**

      * fig: matplotlib figure instance

    """

    if foldover:
        bsize = bstruct.shape
        temp = np.zeros((bsize[0], bsize[1]*2-1))
        print temp.shape, bsize
        temp[:, bsize[1]-1:] = bstruct
        mirror_idx = np.arange(bsize[1]-1, 0, -1)
        temp[:, :bsize[1]-1] = bstruct[:, mirror_idx]
        bstruct = temp
        k_quasi = np.linspace(-1, 1, num=bstruct.shape[1])
    else:
        k_quasi = np.linspace(0, 1, num=bstruct.shape[1])

    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i in range(nbands):
        ax.plot(k_quasi, bstruct[i, :])

    ax.set_xlabel(r'$qa/\pi$')
    ax.set_ylabel(r'$E (E_r)$')

    return fig