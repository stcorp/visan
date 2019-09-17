# This is an example VISAN script for the gammap() function.

# This example shows the gammap function (= gamma(a,x) / Gamma(a)) for
# several values of 'a'.

from visan.math import gammap


def run():

    x = numpy.arange(1500.) / 100
    x = x[1:]
    a = numpy.ones(numpy.shape(x), dtype=float)
    y = gammap(0.5 * a, x)
    w = plot(x, y, name='a=0.5')
    y = gammap(1.0 * a, x)
    plot(x, y, name='a=1.0', window=w)
    y = gammap(3.0 * a, x)
    plot(x, y, name='a=3.0', window=w)
    y = gammap(10.0 * a, x)
    plot(x, y, xrange=(0, 15), yrange=(0, 1), name='a=10.0', window=w, title='gammap() example')


run()
