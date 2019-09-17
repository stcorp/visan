# This is an example VISAN script for the lfit() function.

from visan.math import lfit


def run():

    # Create 5 sample points
    x = numpy.array([0, 1, 2, 3, 4])
    y = numpy.array([1, 3, 2, 5, 4])
    w = plot(x, y, lines=False, points=True, name="measurements")

    # We are going to plot our fitted functions using 50 points in the range [0,5)
    xh = numpy.arange(50.) / 10

    # Fit the sample points using the function:
    #     y = a1 + a2 * x
    def F(x):
        return numpy.array([numpy.ones(numpy.shape(x), dtype=float), x])
    a = lfit(x, y, F)
    plot(xh, numpy.dot(a, F(xh)), window=w, name="first order fit")

    # Fit the sample points using the function:
    #     y = a1 + a2 * x + a2 * x^2
    def F(x):
        return numpy.array([numpy.ones(numpy.shape(x), dtype=float), x, x * x])
    a = lfit(x, y, F)
    plot(xh, numpy.dot(a, F(xh)), window=w, name="second order fit")

    # Fit the sample points using the function:
    #     y = a1 + a2 * x + a2 * x^2 + a3 * x^3
    def F(x):
        return numpy.array([numpy.ones(numpy.shape(x), dtype=float), x, x * x, x ** 3])
    a = lfit(x, y, F)
    plot(xh, numpy.dot(a, F(xh)), window=w, name="third order fit")

    # Fit the sample points using the function:
    #     y = a1 + a2 * x + a2 * x^2 + a3 * x^3 + a4 * x^4
    def F(x):
        return numpy.array([numpy.ones(numpy.shape(x), dtype=float), x, x * x, x ** 3, x ** 4])
    a = lfit(x, y, F)
    plot(xh, numpy.dot(a, F(xh)), window=w, name="fourth order fit", title="lfit() example")


run()
