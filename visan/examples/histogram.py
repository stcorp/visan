# This is an example VISAN script for the histogram() function.

from visan.math import histogram


def run():

    # We will calculate a series of means
    num_means = 10000
    # Each mean will be calculated using sample set of uniformly distributed
    # values in the range [0,1]
    num_samples_per_mean = 10
    # We will use a number of bins to create a histogram showing the
    # distribution of all the means
    num_bins = 200

    # We first create all samples for all means
    values = numpy.random.random(num_means * num_samples_per_mean)
    # The we reshape the array to a matrix
    values.shape = [num_means, num_samples_per_mean]

    # Calculate the means
    means = numpy.zeros(num_means, dtype=float)
    for i in range(num_means):
        means[i] = values[i, :].mean()

    # Create the array with the edges of the bins
    bins = numpy.array(list(range(num_bins + 1)), dtype=float) / num_bins

    # Create the histogram
    h = histogram(means, bins)

    # Plot the histogram
    histogramplot(h, bins, title="Distribution of means using uniformly distributed random variables on [0,1]")


run()
