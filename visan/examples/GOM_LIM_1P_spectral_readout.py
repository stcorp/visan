# This is an example VISAN script for the GOM_LIM_1P product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing GOM_LIM_1P products.

# This example will then take the first product it finds in this directory and
# for that product plot the background spectra


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir starting with 'GOM_LIM_1P'
    files = glob.glob(os.path.join(productdir, "GOM_LIM_1P*"))
    if len(files) == 0:
        print(("Could not find any GOM_LIM_1P files in directory '" + productdir + "'"))
        return

    # We only ingest the first file from the list
    corup = harp.import_product(files[0], "", "spectra=upper")
    nocorup = harp.import_product(files[0], "", "spectra=upper;corrected=false")
    corlow = harp.import_product(files[0], "", "spectra=lower")
    nocorlow = harp.import_product(files[0], "", "spectra=lower;corrected=false")

    w = plot(nocorup, name="upper without correction")
    plot(corup, name="upper with correction", window=w)
    plot(nocorlow, name="lower without correction", window=w)
    plot(corlow, name="lower with correction", window=w, title="GOM_LIM_1P background spectra example")


run()
