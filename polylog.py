r"""Functions that approach several polylogarithms by polynomials.

Precision is on the order of 1e-7 or better. For working with fermions, the
polylog functions Li(x) are usually used in the form -Li(-exp(x)). We therefore
define functions fermi_poly as:
fermi_poly_s(x) :math:`=-Li_s(-e^x)`,
with :math:`Li_s(z)=\sum_{k=1}^{\infty}\frac{z^k}{k^s}`.
This is useful if you are only dealing with Fermi statistics. For working with
bose statistics we define g-functions in a similar way.

There is a more accurate and general algorithm in lerch.py for Li_s(x),
that works for all s>0, the polynomial approximations in this file are much
faster however.

"""


import numpy as np


def fermi_poly3(x):
    """fermi_poly3(x), equal to -Li_3(-e^x)"""

    def f0(x):
        return np.exp(x)
    def f1(x):
        ex = np.exp(x)
        return (1 + (-0.125 + (0.037037037037037035 + (-0.015625 + (0.008 - 0.004629629629629629*ex)*ex)*ex)*ex)*ex)*ex
    def f2(x):
        x2 = x**2
        return 0.9015426773696955 + (0.8224670334241131 + (0.34657359027997264 + (0.08333333333333333 + (0.010416666666666666 +(-0.00017361111111111112 + (6.200396825396825e-6 +(-2.927965167548501e-7 + (1.6179486665597777e-8 + (-9.90785651003905e-10 + (6.525181428041877e-11 +(-4.5372283133067906e-12 + 3.290608283068484e-13*x2)*x2)*x2)*x2)*x2)*x2)*x2)*x2)*x)*x)*x)*x
    def f3(x):
        invex = np.exp(-x)
        return (((((0.008*invex - 0.015625)*invex + 0.037037037037037035)*invex) - 0.125)*invex + 1)*invex + 1.6449340668482262*x + 0.16666666666666666*x**3
    def f4(x):
        return 1.6449340668482262*x + 0.16666666666666666*x**3

    # fix for bug in piecewise, fixed in more recent numpy
    if np.isscalar(x):
        x = np.array([x], dtype=float)
    # define piecewise function and evaluate
    ans = np.piecewise(x, [x<=-20, np.logical_and(x>-20, x<=-2), \
                       np.logical_and(x>-2, x<=2), np.logical_and(x>2, x<=20)],\
                       [f0, f1, f2, f3, f4])
    return ans


#def polylog5half(x):
    #"""Polylog(5/2,x), equal to -Li_{5/2}(-e^x)"""
    #if (x<=-20.):
        #if (np.exp(x)==0): #WTF?
            #return 1e-9
        #else:
            #return np.exp(x)
    #elif (x<=-2.):
        #ex = np.exp(x)
        #return (1 + (-0.17677669529663687 + (0.06415002990995843 - (0.03125 + (0.01788854381999832 - (0.011340230290662863 + (0.007713560673657698 - (0.005524271728019902 + (0.00411522633744856 - 0.0031622776601683794*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex
    #elif (x<=2.):
        #res = (7.999472242952045e-8 + (2.015789875039643e-8 + (-5.182488893752819e-9 + (-1.3550552937770878e-9 + (3.5944104666022113e-10 + (9.653703483078106e-11 + (-2.6209625544677692e-11 + (-7.185930974961928e-12 + (1.9812061650792594e-12 + 5.447084984800099e-13*x)*x)*x)*x)*x)*x)*x)*x)*x)*x
        #return 0.8671998890121841+(0.7651470246254081+(0.30244932171081546+(0.06335080210161399+(0.0049450362799933825+(-0.0007320093393446121+(-0.00013339945006254949  + (0.000027147085179903566+(5.930588304137955e-6+(-1.3626304577484817e-6 + (-3.252451788607287e-7 + res*x)*x)*x)*x)*x)*x)*x)*x)*x)*x)*x
    #elif (x<=12.):
        #res = 5.992860912139351e-7 + (-6.083668666935579e-8 + (5.041252634789406e-9  + (-3.386896134140133e-10 + (1.8196669171414837e-11 + (-7.642990316874879e-13 + (2.4202106712129105e-14 + (-5.437364923509245e-16 + (7.72925401611516e-18 -5.228771407811986e-20*x)*x)*x)*x)*x)*x)*x)*x)*x
        #return 0.869416215427492 + (0.7603408345815055 + (0.30606614629176887 + (0.06361411550944529 + (0.002145410757189772 + (0.002020072416997651 + (-0.0017045762862650151 + (0.0006382881546811445 + (- 0.00016246851298525836 + (0.00003140383144730955 + (-4.819813947314412e-6+res*x)*x)*x)*x)*x)*x)*x)*x)*x)*x)*x
    #elif (x<=20.):
        #x2 = x**2
        #invex = np.sqrt(x)
        #return (-2.0851412241155116/x/x - 0.5343060576801043)/x/invex + 1.8561093322772355*invex + 0.30090111122547003*x2*invex
    #else:
        #x2 = x**2
        #invex = np.sqrt(x)
        #return 1.8561093322772355*invex + 0.30090111122547003*x2*invex


def fermi_poly5half(x):
    """fermi_poly5half(x), equal to -Li_{5/2}(-e^x)

    FAILS TESTS (COMPARING TO LERCH), DO NOT USE WITHOUT INVESTIGATING MORE

    """

    def f0(x):
            return np.exp(x)
    def f1(x):
        ex = np.exp(x)
        return (1 + (-0.17677669529663687 + (0.06415002990995843 - (0.03125 + (0.01788854381999832 - (0.011340230290662863 + (0.007713560673657698 - (0.005524271728019902 + (0.00411522633744856 - 0.0031622776601683794*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex
    def f2(x):
        res = (7.999472242952045e-8 + (2.015789875039643e-8 + (-5.182488893752819e-9 + (-1.3550552937770878e-9 + (3.5944104666022113e-10 + (9.653703483078106e-11 + (-2.6209625544677692e-11 + (-7.185930974961928e-12 + (1.9812061650792594e-12 + 5.447084984800099e-13*x)*x)*x)*x)*x)*x)*x)*x)*x)*x
        return 0.8671998890121841+(0.7651470246254081+(0.30244932171081546+(0.06335080210161399+(0.0049450362799933825+(-0.0007320093393446121+(-0.00013339945006254949  + (0.000027147085179903566+(5.930588304137955e-6+(-1.3626304577484817e-6 + (-3.252451788607287e-7 + res*x)*x)*x)*x)*x)*x)*x)*x)*x)*x)*x
    def f3(x):
        res = 5.992860912139351e-7 + (-6.083668666935579e-8 + (5.041252634789406e-9  + (-3.386896134140133e-10 + (1.8196669171414837e-11 + (-7.642990316874879e-13 + (2.4202106712129105e-14 + (-5.437364923509245e-16 + (7.72925401611516e-18 -5.228771407811986e-20*x)*x)*x)*x)*x)*x)*x)*x)*x
        return 0.869416215427492 + (0.7603408345815055 + (0.30606614629176887 + (0.06361411550944529 + (0.002145410757189772 + (0.002020072416997651 + (-0.0017045762862650151 + (0.0006382881546811445 + (- 0.00016246851298525836 + (0.00003140383144730955 + (-4.819813947314412e-6+res*x)*x)*x)*x)*x)*x)*x)*x)*x)*x)*x
    def f4(x):
        x2 = x**2
        invex = np.sqrt(x)
        return (-2.0851412241155116/x/x - 0.5343060576801043)/x/invex + 1.8561093322772355*invex + 0.30090111122547003*x2*invex
    def f5(x):
        x2 = x**2
        invex = np.sqrt(x)
        return 1.8561093322772355*invex + 0.30090111122547003*x2*invex

    # fix for bug in piecewise, fixed in more recent numpy
    if np.isscalar(x):
        x = np.array([x], dtype=float)
    # define piecewise function and evaluate
    ans = np.piecewise(x, [x<=-20, np.logical_and(x>-20, x<=-2), \
                       np.logical_and(x>-2, x<=2), np.logical_and(x>2, x<=12), \
                       np.logical_and(x>12, x<=20)], [f0, f1, f2, f3, f4, f5])
    return ans


def fermi_poly2(x):
    """fermi_poly2(x), equal to -Li_2(-e^x)"""

    def f0(x):
        return np.exp(x)
    def f1(x):
        ex = np.exp(x)
        return (1.+( -0.25+( 0.111111+( -0.0625+( 0.04+( -0.0277778+( 0.0204082+( -0.015625+( 0.0123457+( -0.01+( 0.00826446+( -0.00694444+( 0.00591716+( -0.00510204+( 0.00444444+( -0.00390625+( 0.00346021+( -0.00308642+( 0.00277008+ -0.0025*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex
    def f2(x):
        ex = x**2
        return 0.822467+(0.6931471805599453+( 0.25+( 0.04166666666666666+( -0.0010416666666666534+( 0.00004960317460316857+( -2.927965167558005e-6+(1.9415383998507108e-7+( -1.3870999148454729e-8+(1.0440288911003276e-9+(-8.167040926799743e-11+6.5806618711692295e-12*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*x)*x)*x
    def f3(x):
        ex = np.exp(-x)
        return 1.6449340668482262 + 0.5*x**2 - (1.+( -0.25+( 0.111111+( -0.0625+( 0.04+( -0.0277778+( 0.0204082+( -0.015625+( 0.0123457+( -0.01+( 0.00826446+( -0.00694444+( 0.00591716+( -0.00510204+( 0.00444444+( -0.00390625+( 0.00346021+( -0.00308642+( 0.00277008 -0.0025*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex)*ex
    def f4(x):
        return 1.6449340668482262 + 0.5*x**2

    # fix for bug in piecewise, fixed in more recent numpy
    if np.isscalar(x):
        x = np.array([x], dtype=float)

    # define piecewise function and evaluate
    ans = np.piecewise(x, [x<=-20, np.logical_and(x>-20, x<=-1), \
                       np.logical_and(x>-1, x<=1), np.logical_and(x>1, x<=20)],\
                       [f0, f1, f2, f3, f4])

    return ans



def dilog(z):
    """Dilog(x), equal to Li_2(x)

    d = dilog(z) = Li_2(z)
      = -Int From t=0 To t=z    log(1-t) dt/t         for all z.
      =  Sum From n=1 To n=Inf  z**n/n**2               for |z|<=1.

    INPUT  z: real or complex, scalar, vector or matrix.
    OUTPUT d: component-wise dilogarithm of z.

    References:
    [1] Lewin, L. 1958. Dilogarithms and associated functions. Macdonald.
    [2] Wood, D. C. 1992. Technical Report 15-92. University of Kent computing laboratory.
    [3] http://en.wikipedia.org/wiki/Polylog

    Didier Clamond, February 28th, 2006.

    """

    # Initialization.
    d  = np.zeros(size(z))
    s  = np.ones(size(z))

    # For large moduli: Mapping onto the unit circle |z|<=1.
    j = np.where(np.abs(z)>1)
    d[j] = -1.64493406684822643 - 0.5*np.log(-z[j])**2
    s[j] = -s[j]
    z[j] = 1./z[j]

    # For large positive real parts: Mapping onto the unit circle with Re(z)<=1/2.
    j = np.where(real(z)>0.5)
    d[j] = d[j] + s[j]*( 1.64493406684822643 - np.log((1-z[j])**(np.log(z[j]))))
    s[j] = -s[j]
    z[j] = 1 - z[j]

    # Transformation to Debye function and rational approximation.
    z = -np.log(1-z)
    s = s*z
    d = d - 0.25*s*z
    z = z**2
    s = s*(1+z*(6.3710458848408100e-2+z*(1.04089578261587314e-3+z*4.0481119635180974e-6)))
    s = s/(1+z*(3.5932681070630322e-2+z*(3.20543530653919745e-4+z*4.0131343133751755e-7)))
    d = d + s
    return d

# g_5/2 function approximated by an 18th degree polynomial.  note, it is not the first 18 terms in the series expansion for g_5/2(x).
# using the first 18 terms would systematically put all the error near x=1 and none of the error near x=0.
def g5halves(x):
    """g5halves(x), equal to -g_{5/2}(-e^x)"""
    if (x<1e-4):
        return x
    else:
        return 0.999856*x + 0.179586*x**2 + 0.0296957*x**3 + 0.328735*x**4 -1.90262*x**5 + 9.61982*x**6 - 38.0899*x**7  + 121.384*x**8 - 313.11*x**9 +655.703*x**10 - 1112.32*x**11 + 1517.67*x**12 - 1643.55*x**13 + 1382.29*x**14 -871.741 *x**15 + 388.521 *x**16 - 109.329 *x**17+ 14.6478*x**18


# This is the g2-function, approximated by a piecewise defined function, each piece being a series expansion of 20th degrees around x = 0.35 and x = 0.9.
# Largest error is at "1": -0.005. At "0.98" it is already down to -8.2E-6.
# Standard Deviation from the "real" g2 is 2.5E-8. This should be good enough ;-)
def g_two(x):
    """g_two(x), equal to -g_2(-e^x)"""
    if (x<1e-4):
        return x
    elif (x<=0.82):
        xp = -0.35+x
        res = (0.49915291366412107+ (0.6328253123804949 + (0.81609574001162  + (1.0675943847818847 +	(1.413674598740013  + (1.89162489083520825 +  (2.554295058361196 +  (3.4767564222154945 + (4.765898838137037 +  (6.574283048568486 + 9.120156359601541*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp
        return (0.38660594116058644+ (1.2308083316927263  + (0.43950458109830315  +   (0.2899264671105867+  (0.24571211455256878  +  (0.23866441621304754 +  (0.2525638070139697 + (0.28346805806862585 + (0.33208947069236144 + (0.4019515561735721 + res)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)
    else:
        xp = -0.9+x
        res = (1.0976006258704519e7 + (8.992322600130886e7 + (7.501623708235847e8 + (6.35310981909834e9 + (5.449526520495981e10 + (4.725869207398318e11 + (4.137351587192319e12 + (3.6523031019929805e13 + (3.247815687554126e14 + (2.9069875624537055e15 + 2.6171279210392548e16*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp
        return 1.2997147230049588 + (2.5584278811044956 + (4.134206732719726 + (15.456143160948358 + (79.71247329180234 + (484.7000237406208 + (3254.9073854253556 + (23355.114659383304 + (175706.33693829825 + (1.36967275364119e6 + res)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp

# This is the g3-function, approximated by a piecewise defined function, each piece being a series expansion of 20th degrees around x = 0.35 and x = 0.9.
# Largest error is at "1": -0.000013. At "0.98" it is already down to -3.8E-8.
def g_three(x):
    """g_three(x), equal to -g_3(-e^x)"""
    if (x<1e-4):
        return x
    elif (x<=0.82):
        xp = -0.35+x
        res = (0.0396957603891595 + (0.04670760669864216 + (0.05617680434859797 + (0.0688359037828904 + (0.08570894194968269 + (0.10821263549305878 + (0.13830133228577052 + (0.17867204142073595 + (0.2330529526732962 + 0.30661105212057754*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp
        return 0.367187924868168 + (1.1045884033159612 + (0.18031418339537875 + (0.07512020410242393 + (0.04611846771665166 + (0.03499328210626231 + (0.030332383657974384 + (0.02880387961885722 + (0.02922889312039987 + (0.031193119279524506 + (0.03463242361601278 + res)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp
    else:
        xp = -0.9+x
        res = (974070.3442266576 + (7.3341159458162645e6 + (5.6594271749896556e7 + (4.458241497102925e8 + (3.574350156223386e9 + (2.909525474975562e10 + (2.399887262219758e11 + (2.002668066305938e12 + (1.6885002547479885e13 + 1.4367625078064384e14*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp
        return 1.04965895018644 + (1.4441274700055098 + (0.6190557839438808 + ( 1.0726278388266532 + (3.399516567907888 + (14.692090448926841 + (76.15547620296046 + (444.122940985332 + (2811.9797322897193 + (18914.876429627224 + ( 133270.98508606057 + res)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp)*xp


g2 = np.vectorize(g_two)
g52 = np.vectorize(g5halves)
g3 = np.vectorize(g_three)