# Copyright (C) 2002-2019 S[&]T, The Netherlands.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
A collection of mathematical functions for VISAN.

  histogram()
  fit()
  lfit()
  gammap()
  gammaq()
  gammaln()
  ecef_to_wgs84()
  wgs84_to_ecef()
"""

import numpy as np
import numpy.linalg as linalg
from functools import reduce


def histogram(a, bins, mode='inner'):
    """ Create a histogram for a set of values using a specified set of bins.

    This function creates a histogram for the values in the array 'a'.
    The bins are defined by the edge values in the 'bins' array.
    The values in 'bins' should be stored in ascending order.

    If mode is 'inner' then len(bins)-1 bins will be used. If mode is 'outer'
    then two more bins are added; one for all values below bins[0] and one for
    the values in 'a' higher then bins[-1].

    Both 'a' and 'bins' should be one dimensional arrays.

    Example:

    >>> histogram([2.1, 4.5, 5, 7.8, 2.5, 6.1, 9.9, 5.1, 5.2, 7.2], arange(11))
    array([0, 2, 0, 1, 3, 1, 2, 0, 1, 0])
    """
    def accumulate(n, i):
        n[i] += 1
        return n
    a = np.asarray(a)
    bins = np.asarray(bins)
    indices = np.searchsorted(bins.flat, a.flat)
    n = reduce(accumulate, indices, np.zeros(len(bins.flat) + 1))
    if mode == 'inner':
        return n[1:-1]
    elif mode == 'outer':
        return n
    else:
        raise ValueError("Invalid value for 'mode' argument")


def fit(x, y, sigy=None, error=False):
    """ Perform a linear fit on a range of x and y values.

    This function fits a set of data points x, y with individual standard
    deviations sigy for the y values to a straight line y = a + bx by
    minimizing chi-square.

    If the 'error' parameter is False the function returns only the found
    values for 'a' and 'b' as a tuple. If 'error' is True then a third tuple
    item is returned containing a dictionary of error statistics ('siga' the
    standard deviation of 'a', 'sigb' the standard deviation of 'b', 'chi2'
    the value of chi-square, and 'q' the goodness of fit probability).

    If 'sigy' is 'None' then no standard deviations are used, 'q' will be 1.0
    and the normalization of chi-square is to unit standard deviation for all
    points.

    Example:

    >>> a, b, err = fit([1.1, 1.95, 3.05], [1, 2.01, 2.95], error=True)
    """
    # This routine is based on an algorithm from Numerical Recipes
    x = np.asarray(x).astype(float)
    y = np.asarray(y).astype(float)
    if x.size != y.size:
        ValueError("Arrays 'x' and 'y' have different length")
    if x.size < 2:
        raise ValueError("Arrays 'x' and 'y' should have at least 2 elements")
    useWeights = False
    if sigy is not None:
        sigy = np.asarray(sigy)
        if sigy.size != y.size:
            raise ValueError("Arrays 'sigy' and 'y' have different length")
        useWeights = True

    # We need to minimize:
    #
    #  chi2 = sum( ((y[i] - a - b * x[i]) / sigy[i])^2 ; i=1..N)
    #
    # When taking derivatives with respect to a and b we get
    #
    #  dchi2/da = 0 = -2 * sum( (y[i] - a - b * x[i]) / sig[i]^2 ; i=1..N)
    #  dchi2/db = 0 = -2 * sum( x[i] * (y[i] - a - b * x[i]) / sig[i]^2 ; i=1..N)
    #
    # which provides us with a linear equation that we can use to solve a and b

    if useWeights:
        weights = 1 / (np.square(sigy.flat))
        S = np.sum(weights)
        Sx = np.dot(x.flat, weights)
        Sy = np.dot(y.flat, weights)
        t = x.flat - Sx / S
        tw = t * weights
        Stt = np.dot(tw, t)
        b = np.dot(tw, y.flat) / Stt
    else:
        S = x.size
        Sx = np.sum(x.flat)
        Sy = np.sum(y.flat)
        t = x.flat - Sx / S
        Stt = np.dot(t, t)
        b = np.dot(t, y.flat) / Stt

    a = (Sy - Sx * b) / S

    if not error:
        return (a, b)

    siga = np.sqrt((1 + Sx * Sx / (S * Stt)) / S)
    sigb = np.sqrt(1 / Stt)
    chi2 = 0.0
    q = 1.0
    if useWeights:
        chi = (y - a - b * x.flat) / sigy.flat
        chi2 = np.dot(chi, chi)
        if x.size > 2:
            q = gammaq(0.5 * (x.size - 2), 0.5 * chi2)
    else:
        chi = y.flat - a - b * x.flat
        chi2 = np.dot(chi, chi)
        if x.size > 2:
            sigdat = np.sqrt(chi2 / (x.size - 2))
            siga *= sigdat
            sigb *= sigdat

    return (a, b, {'siga': siga, 'sigb': sigb, 'chi2': chi2, 'q': float(q)})


def lfit(x, y, F, sigy=None, error=False):
    """ Perform a fit on a range of values using a set of basis functions.

    This function fits a set of data points x, y with individual standard
    deviations sigy for the y values to a linear combination of basis functions
    y = sum(a_i * F_i(x); i = 1..N) minimizing chi-square.

    F should be a user provided function F(x) that returns an array where each
    element is the evaluation of the basis function F_i() at location 'x'

    The function 'lfit' will return an array 'a' with the coefficients for the
    basis functions F_i().

    If the 'error' parameter is False the function returns only the found
    values for 'a' as an array. If 'error' is True then a tuple is returned
    containing the array 'a', the covariance matrix, and the value of
    chi-square.

    If 'sigy' is 'None' then the standard deviations for all y values are set
    to 1.0.

    Example:

    >>> def F(x):
    ...    return array([1, x, x*x])
    >>> a, covar, chi2 = lfit([0, 1, 2, 3], [1, 3, 2, 1], F, error=True)
    >>> y = dot(a, F(0.5))
    """
    x = np.asarray(x).astype(float)
    y = np.asarray(y).astype(float)
    numx = np.shape(x)[0]
    if numx != y.size:
        raise ValueError("Incompatible number of 'x' and 'y' values")
    testy = F(x[0])
    if testy.ndim != 1:
        raise ValueError("Function 'F' should return a one dimensional array")
    N = testy.size
    if N > y.size:
        # We have more unknowns then measurements
        raise ValueError("Arrays 'x' and 'y' should have at least %i elements" % (testy.size))
    if sigy is not None:
        sigy = np.asarray(sigy).astype(float)
        if np.shape(sigy) != np.shape(y):
            raise ValueError("Arrays 'y' and 'sigy' should have the same shape")
    else:
        sigy = np.ones(np.shape(y), float)

    A = np.zeros((numx, N), float)
    b = np.zeros((numx), float)
    for k in range(numx):
        A[k] = F(x[k]) / sigy[k]
        b[k] = y[k] / sigy[k]
    a, chi2, rankA, svA = np.linalg.lstsq(A, b, rcond=None)

    if not error:
        return a

    covar = np.matrixmultiply(np.transpose(A), A)

    return (a, covar, chi2)


def gammap(a, x):
    """The incomplete gamma function P(a,x) (= gamma(a,x) / Gamma(a) )."""
    # This routine is based on an algorithm from Numerical Recipes
    a = np.asarray(a).astype(float)
    x = np.asarray(x).astype(float)

    if np.sometrue(x < 0):
        raise ValueError("Parameter 'x' may not contain negative value(s)")
    if np.sometrue(a <= 0):
        raise ValueError("Parameter 'a' may not have value(s) <= 0")
    if np.shape(a) != np.shape(x):
        raise ValueError("Parameters 'a' and 'x' should have the same shape")

    gp = np.zeros(np.shape(x), dtype=float)
    criterium = x.flat < np.add(a.flat, 1.0)
    serids = np.nonzero(criterium)[0]
    if serids.size > 0:
        gp.flat[serids] = _gammaBySeries(a.flat[serids], x.flat[serids])
    cfrids = np.nonzero(1 - criterium)[0]
    if cfrids.size > 0:
        gp.flat[cfrids] = 1.0 - _gammaByContinuedFractions(a.flat[cfrids], x.flat[cfrids])
    return gp


def gammaq(a, x):
    """The incomplete gamma function Q(a,x) = 1 - P(a,x) (= 1 - gamma(a,x) / Gamma(a) )."""
    # This routine is based on an algorithm from Numerical Recipes
    a = np.asarray(a).astype(float)
    x = np.asarray(x).astype(float)

    if np.sometrue(x < 0):
        raise ValueError("Parameter 'x' may not contain negative value(s)")
    if np.sometrue(a <= 0):
        raise ValueError("Parameter 'a' may not have value(s) <= 0")
    if np.shape(a) != np.shape(x):
        raise ValueError("Parameters 'a' and 'x' should have the same shape")

    gq = np.zeros(np.shape(x), dtype=float)
    criterium = x.flat < np.add(a.flat, 1.0)
    serids = np.nonzero(criterium)[0]
    if serids.size > 0:
        gq.flat[serids] = 1.0 - _gammaBySeries(a.flat[serids], x.flat[serids])
    cfrids = np.nonzero(1 - criterium)[0]
    if cfrids.size > 0:
        gq.flat[cfrids] = _gammaByContinuedFractions(a.flat[cfrids], x.flat[cfrids])
    return gq


def _gammaBySeries(a, x):
    # This routine is based on an algorithm from Numerical Recipes
    # This function assumes that 'a' and 'x' are numpy arrays with rank 1 and
    # equal lenghts
    ITMAX = 100
    EPS = 3.0e-7
    lnga = gammaln(a)
    ap = a.copy()
    d = 1.0 / a
    s = d.copy()
    for n in range(ITMAX):
        ap += 1
        d *= x / ap
        s += d
        if np.alltrue(np.fabs(d) < np.fabs(s) * EPS):
            return s * np.exp(-x + a * np.log(x) - lnga)
    raise ValueError("Parameter 'a' has value(s) that are too large")


def _gammaByContinuedFractions(a, x):
    # This routine is based on an algorithm from Numerical Recipes
    # This function assumes that 'a' and 'x' are numpy arrays with rank 1 and
    # equal lenghts
    ITMAX = 100
    EPS = 3.0e-7
    FPMIN = 1.0e-300
    lnga = gammaln(a)
    b = x + 1.0 - a
    c = 1.0 / FPMIN
    d = 1.0 / b
    h = d.copy()
    for n in range(ITMAX):
        i = n + 1
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        d[np.nonzero(np.fabs(d) < FPMIN)[0]] = FPMIN
        c = b + an / c
        c[np.nonzero(np.fabs(c) < FPMIN)[0]] = FPMIN
        d = 1.0 / d
        dl = d * c
        h *= dl
        if (np.alltrue(np.fabs(dl - 1.0) < EPS)):
            return h * np.exp(-x + a * np.log(x) - lnga)
    raise ValueError("Parameter 'a' has value(s) that are too large")


def gammaln(x):
    """Returns the value of ln(Gamma(x))."""
    # We use Lanczos approximation
    x = np.asarray(x).astype(float)
    if np.sometrue(x <= 0):
        raise ValueError("Parameter 'x' may not have value(s) <= 0")

    c = (1.000000000000000174663,
         5716.400188274341379136,
         -14815.30426768413909044,
         14291.49277657478554025,
         -6348.160217641458813289,
         1301.608286058321874105,
         -108.1767053514369634679,
         2.605696505611755827729,
         -0.7423452510201416151527e-2,
         0.5384136432509564062961e-7,
         -0.4023533141268236372067e-8)
    g = 9
    t = np.add(x.flat, g)
    s = c[0]
    for k in np.arange(g + 1, 0, -1):
        # going from g+1 to 1 with stepsize -1
        s += c[k] / t
        t -= 1
    ss = np.add(x.flat, g - 0.5)
    f = np.log(2.5066282746310005 * s) + np.add(x.flat, -0.5) * np.log(ss) - ss
    return np.reshape(f, np.shape(x))


def ecef_to_wgs84(x, y, z):
    """ Convert XYZ coordinates in Earth-Centered Earth-Fixed (ECEF) to WGS84 lat/lon/height """
    # WGS84 semi-major axis (a) and semi-minor axis (b)
    a = 6378137
    b = 6356752.31424518
    e = np.sqrt((a * a - b * b) / (a * a))
    e_prime = np.sqrt((a * a - b * b) / (b * b))
    p = np.sqrt(x * x + y * y)
    teta = np.arctan2(z * a, p * b)
    sin_teta = np.sin(teta)
    cos_teta = np.cos(teta)
    lon = np.arctan2(y, x)
    lat = np.arctan2(z + e_prime * e_prime * b * sin_teta * sin_teta * sin_teta,
                     p - e * e * a * cos_teta * cos_teta * cos_teta)
    N = a / np.sqrt(1 - e * e * np.sin(lat) * np.sin(lat))
    h = p / np.cos(lat) - N
    lat = lat * 180.0 / pi
    lon = lon * 180.0 / pi
    return lat, lon, h


def wgs84_to_ecef(lat, lon, h):
    """ Convert WGS84 lat/lon/height to XYZ coordinates in Earth-Centered Earth-Fixed (ECEF) """
    # WGS84 semi-major axis (a) and semi-minor axis (b)
    a = 6378137
    b = 6356752.31424518
    lat = lat * pi / 180.0
    lon = lon * pi / 180.0
    e = np.sqrt((a * a - b * b) / (a * a))
    N = a / np.sqrt(1 - e * e * np.sin(lat) * np.sin(lat))
    x = (N + h) * np.cos(lat) * np.cos(lon)
    y = (N + h) * np.cos(lat) * np.sin(lon)
    z = (b * b * N / (a * a) + h) * np.sin(lat)
    return x, y, z
