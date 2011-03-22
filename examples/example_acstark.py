"""This example calculates the light shift in an optical dipole trap.

A range of relevant wavelengths (532 to 1064 nm) are used. Laser power
is 1W and trap waist is 100 um.
The result for the light shift is given in recoil energies, which are
the recoils from the ODT light, not the resonant frequencies.

"""

import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

from odysseus.analysis import atoms, lightshift, lattice


# define atoms we are interested in
li = atoms.Li6()
na = atoms.Na()
cs = atoms.Cs()
rb = atoms.Rb85()
k40 = atoms.K40()
species = [li, na, cs, rb, k40]

# calculate
shifts = {}
wavelengths = np.linspace(532e-9, 1064e-9, num=500)
for atom in species:
    shifts[atom.name] = lightshift.acstark(wavelengths, 1, 100e-6, atom)\
          / lightshift.recoil_energy(wavelengths, atom.mass)

# plot the result
fig = plt.figure()
ax = fig.add_subplot(111)
for atom in species:
    ax.plot(wavelengths*1e9, shifts[atom.name], label=atom.name)
ax.set_xlabel(r'$\lambda_{ODT}$ (nm)')
ax.set_ylabel(r'$V_0$ $(E_r)$')
ax.set_ylim(-150, 250)
ax.legend(loc=4)

plt.show()