import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

from odysseus.analysis import lightshift, lattice


def plot_energies(gaps, widths, tJs, secband, depths):
    """Show several energy scales as a function of lattice depth"""

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(depths, gaps, label=r'bandgap')
    ax.plot(depths, widths, label=r'bandwidth')
    ax.plot(depths, tJs, label=r'tJ')
    ax.plot(depths, secband, label=r'bottom second band')
    ax.plot(depths, depths, 'k--', label=r'lattice depth')

    ax.set_xlabel(r'$U_0$ ($E_r$)')
    ax.set_ylabel(r'$E$ ($E_r$)')
    ax.legend(loc=2)

    return fig


# create empty arrays
num = 25
depths = np.linspace(0, 6, num=num)
gaps = np.zeros(num)
widths = np.zeros(num)
tJs = np.zeros(num)
secband = np.zeros(num)

# calculate energies
for i, depth in enumerate(depths):
    bstruct, bandwidth, bandgap, tJ = lattice.latt_energies(depth)
    secondband = bstruct[1, :].min()
    gaps[i] = bandgap
    widths[i] = bandwidth
    tJs[i] = tJ
    secband[i] = secondband

# plot results
fig1 = plot_energies(gaps, widths, tJs, secband, depths)
fig2 = lattice.plot_bands(bstruct)
plt.show()