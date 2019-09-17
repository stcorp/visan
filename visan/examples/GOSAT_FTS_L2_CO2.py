# This is an example VISAN script for the GOSAT FTS L2 CO2 product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing GOSAT FTS L2 CO2 products.

# This example will then take all products it finds in this directory and
# for those product plot the CO2 columns


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all GOSAT FTS L2 C01S files in productdir
    files = glob.glob(os.path.join(productdir, "GOSATTFTS*02C01S*"))
    if len(files) == 0:
        print(("Could not find any GOSAT FTS L2 C01S files in directory '" + productdir + "'"))
        return

    product = harp.import_product(files)
    wplot(product, title="GOSAT FTS L2 CO2")


run()
