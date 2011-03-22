"""Module of routines for computing the Lerch Trancident and related
functions.

This file is only used to check the polynomial implementation in polylog.py
for correctness.

Written by Michael Forbes.

"""

#__all__ = ['LerchPhi','Li']

from numpy import isreal,iscomplex, inf, finfo
from scipy.integrate import quad
from scipy.special import gamma
import math
import cmath

import numpy as np

_eps = finfo(type(1.0)).eps
_epsrel = _eps*64
_epsabs = 0.0


def LerchPhi_real(z,s,a):
    """Return the Lerch Trancident Phi(z,s,a) for real arguments (see
    LerchPhi for more details.

    Computes the result using the integral representation
    Phi(z,s,a) = 1/\Gamma(s)*\int_0^\infty dt t^{s-1}e^{-at}/(1-ze^{-t})

    The following analysis is for real arguments: complex values may
    mess up the integration.

    The asymptotics of the integrand are:
    Near t == 0:
    * If z != 1: t^{s-1}
    * If z == 1: t^{s-2}
    Near t == inf:
    * t^{s-1}e^{-at}
    In addition, if 1 < z then there is an additional pole at
    t = t0 = -log(1/z): ~ 1/(t-t0)

    The asymptotics dictate that the integral is convergent iff:

    (0 < a) and ((z != 1 and 0 < s) or (z == 1 and 1 < s))

    For speed, however, we assume that the calling routine has checked
    for convergence.

    The Lerch function is actually defined for smaller

    The integrand only switches sign if z > 1 in which case we use the
    'cauchy' form of the adaptive quad integrator to deal with the
    pole.  The only potential for roundoff is in the computation of
    the denominator if z*exp(-t) ~ 1.

    The integrand is:
    exp((s-1)*log(t)-a*t)/(1-z*exp(-t))

    """

    # We break up the integral using 1/a as the length scale
    # because quad can't handle both infinite range and a
    # singularity.
    b0 = max(1./a,1.0)

    if z < 1.0:
        # Here we use the asymptotic forms of quad with power-law
        # divergences at the endpoints:
        # integrand = (t-a0)**alpha*(t-b0)**beta*f()
        # where a0 and b0 are the endpoints.
        #
        alpha = s-1.0
        beta = 0.0

        # Determine cutoff for approximation
        cutoff = (720.0*_eps)**(0.25)
        def f1(t,s=s,a=a,cutoff=cutoff,exp=math.exp):
            # This should be computed robustly for small z and t
            return exp(-a*t)/(1.0-z*exp(-t))
    elif z == 1.0:
        # Here we use the asymptotic forms of quad with power-law
        # divergences at the endpoints:
        # integrand = (t-a0)**alpha*(t-b0)**beta*f()
        # where a0 and b0 are the endpoints.
        #
        # We break up the integral using 1/a as the length scale
        # because quad can't handle both infinite range and a
        # singularity.
        alpha = s-2.0
        beta = 0.0

        # Determine cutoff for approximation
        cutoff = (720.0*_eps)**(0.25)
        def f1(t,s=s,a=a,cutoff=cutoff,exp=math.exp):
            # Compute t/(1.0-exp(-t)) robustly using series expansion:
            # 1 + t/2 + t**2/12 - t**4/720
            # It alternates beyond this point.
            if t < cutoff:
                factor = 1.0 + t*(0.5 + t/12.0)
            else:
                factor = t/(1.0-exp(-t))
            return exp(-a*t)*factor
    else:
        raise Exception("Not supported yet.")

    (result1,err1) = quad(f1,0,b0,epsabs=_epsabs,epsrel=_epsrel,
                          weight='alg',wvar=(alpha,beta))

    def f(t,s=s,a=a,exp=math.exp,log=math.log):
        """Integrand"""
        return exp((s - 1.0)*log(t) - a*t)/(1.0 - z*exp(-t))

    (result2,err2) = quad(f,b0,inf,epsabs=_epsabs,epsrel=_epsrel)

    result = result1+result2
    err = math.sqrt(err1*err1+err2*err2)

    return result/gamma(s)


def LerchPhi(z,s,a):
    """Return the Lerch Trancident function Phi(z,s,a) on a restricted
    domain.

    Phi(z,s,a) = \sum_{n=0}^\infty \frac{z^n}{(n+a)^s}

    Computes the result using the integral representation

    Phi(z,s,a) = 1/\Gamma(s)*\int_0^\infty dt t^{s-1}e^{-at}/(1-ze^{-t})

    """

    #Special Cases:
    if isreal(a) and isreal(s) and isreal(z) and \
            ((0 < a) and (((0 < s) and (z < 1)) or
                          ((1 < s) and (1 == z)))):
        return LerchPhi_real(z,s,a)
    else:
        raise Warning("Lerch arguments "+`(z,s,a)`+"not supported.")


def Li(s,z):
    """Return the polylogarithm Li_s(z)."""
    return z*LerchPhi(z,s,1.0)
Li = np.vectorize(Li)