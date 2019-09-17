# This is an example VISAN script for the GOM_TRA_1P product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing GOM_TRA_1P products.

# This example will then take the first product it finds in this directory and
# for that product plot measured spectra


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir starting with 'GOM_TRA_1P'
    files = glob.glob(os.path.join(productdir, "GOM_TRA_1P*"))
    if len(files) == 0:
        print(("Could not find any GOM_TRA_1P files in directory '" + productdir + "'"))
        return

    # We only ingest the first file from the list
    product = harp.import_product(files[0])

    plot(product, yrange=(-1, 2), points=True, pointsize=.5, lines=False, showpropertypanel=True,
         name=os.path.basename(files[0]), title="GOM_TRA_1P spectral readout example", ylabel="")


run()
