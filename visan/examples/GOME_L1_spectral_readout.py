# This is an example VISAN script for the GOME_L1 product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing GOME L1 products (calibrated and converted using the GOME Lvl1 extractor).

# This example will then take the first product it finds in this directory and
# for that product plot the measured spectra


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir ending with '.el1'
    files = glob.glob(os.path.join(productdir, "*.el1"))
    if len(files) == 0:
        print(("Could not find any GOME_L1_EXTRACTED files in directory '" + productdir + "'"))
        return

    # We only ingest the first file from the list
    product = harp.import_product(files[0])

    plot(product, ymin=0, ymax=65535, name=os.path.basename(files[0]), title="GOME_L1 spectral readout example")


run()
