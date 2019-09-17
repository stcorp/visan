# This is an example VISAN script for the GOSAT FTS L1B product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing GOSAT FTS L1B products.

# This example will then take the first product it finds in this directory and
# for that product plot the measured spectra for all bands


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all GOSAT TFTS L1B files in productdir
    files = glob.glob(os.path.join(productdir, "GOSATTFTS*.01"))
    if len(files) == 0:
        print(("Could not find any GOSAT FTS L1b files in directory '" + productdir + "'"))
        return

    # We only ingest data from the first file in the list
    file = files[0]

    band1p = harp.import_product(file, 'wavenumber>=12900;wavenumber<=13200', 'band=1p')
    band1s = harp.import_product(file, 'wavenumber>=12900;wavenumber<=13200', 'band=1s')
    band2p = harp.import_product(file, 'wavenumber>=5800;wavenumber<=6400', 'band=2p')
    band2s = harp.import_product(file, 'wavenumber>=5800;wavenumber<=6400', 'band=2s')
    band3p = harp.import_product(file, 'wavenumber>=4800;wavenumber<=4800', 'band=3p')
    band3s = harp.import_product(file, 'wavenumber>=4800;wavenumber<=4800', 'band=3s')
    band4 = harp.import_product(file, 'wavenumber>=650', 'band=4')

    wplot(band4, title="GOSAT FTS L1b measurement locations")

    w = plot(band1p, name="Band 1 P")
    plot(band1s, name="Band 1 S", title="GOSAT FTS Band 1 P/S", window=w)
    w = plot(band2p, name="Band 2 P")
    plot(band2s, name="Band 2 S", title="GOSAT FTS Band 2 P/S", window=w)
    w = plot(band3p, name="Band 3 P")
    plot(band3s, name="Band 3 S", title="GOSAT FTS Band 3 P/S", window=w)
    plot(band4, name="Band 4", title="GOSAT FTS Band 4")


run()
