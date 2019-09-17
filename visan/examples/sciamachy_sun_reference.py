# This is an example VISAN script that displays Sun Reference Spectra from
# a SCIAMACHY Level 1b product.

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing SCI_NL__1P products.

# This example will then take the first product it finds in this directory and
# for that product plot the sun reference spectra


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all SCIAMACHY L1b files in productdir.
    files = glob.glob(os.path.join(productdir, "SCI_NL__1P*"))
    if len(files) == 0:
        print(("Could not find any SCI_NL__1P files in directory '" + productdir + "'"))
        return

    # Ingest the ozone profile and tangent altitudes from the first SCIAMACHY
    # product file.

    pf = coda.open(files[0])
    if coda.get_product_type(pf) != 'SCI_NL__1P':
        print((files[0] + "is not a SCI_NL__1P file"))
        coda.close(pf)
        return

    num_sun_reference = coda.get_size(pf, 'sun_reference')

    for i in range(num_sun_reference[0]):
        wvlen = coda.fetch(pf, 'sun_reference', i, 'wvlen_sun_meas')

        # value '999' signifies invalid data.
        print((wvlen[0, 0]))
        if wvlen[0, 0] != 999:
            spectrum = coda.fetch(pf, 'sun_reference', i, 'mean_ref_spec')
            w = plot(wvlen[0], spectrum[0], color=(0, 0, 1))
            plot(wvlen[1], spectrum[1], color=(0, 1, 0), window=w)
            plot(wvlen[2], spectrum[2], color=(1, 0, 0), window=w)
            plot(wvlen[3], spectrum[3], color=(1, 0, 1), window=w)
            plot(wvlen[4], spectrum[4], color=(0, 0, 1), window=w)
            plot(wvlen[5], spectrum[5], color=(0, 1, 0), window=w)
            plot(wvlen[6], spectrum[6], color=(1, 0, 0), window=w)
            plot(wvlen[7], spectrum[7], color=(1, 0, 1), window=w, xrange=(200, 2400), ylog=1,
                 xlabel="wavelength [ nm ]", ylabel="photons/\n(m^2.nm.s)",
                 title="GADS sun reference spectrum (GADS %d)" % i)

    coda.close(pf)


run()
