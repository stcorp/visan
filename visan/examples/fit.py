# This is an example VISAN script for the fit() function.

from visan.math import fit

def run():

    # Create some sample x and y data
    x = numpy.random.random(100) * 10.0
    y = numpy.random.random(100) * 10.0
    x = numpy.sort(x)
    y = numpy.sort(y)
    # We give our y values a standard deviation of 0.5
    weights = 0.5 * numpy.ones(numpy.shape(y))

    # Calculate the best guesses for a, b for the linear function y = a + b * x
    a, b, err = fit(x, y, sigy=weights, error=True)

    # Print a, b and the error information
    print(("a = %f, b = %f, siga = %f, sigb = %f, chi2 = %f, q = %f" %
          (a, b, err['siga'], err['sigb'], err['chi2'], err['q'])))

    # Plot the initial values and our fitted linear function
    w = plot(x, y, lines=0, points=1, name="samples")
    plot(x, a + b * x, xmin=-1, xmax=11, ymin=-1, ymax=11, name="fitted line", window=w, title="fit() example")


run()
