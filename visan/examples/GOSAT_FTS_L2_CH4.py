# This is an example VISAN script for the GOSAT FTS L2 CH4 product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing GOSAT FTS L2 CH4 products.

# This example will then take all products it finds in this directory and
# for those product plot the CH4 columns


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all GOSAT FTS L2 C02S files in productdir
    files = glob.glob(os.path.join(productdir, "GOSATTFTS*02C02S*"))
    if len(files) == 0:
        print(("Could not find any GOSAT FTS L2 C02S files in directory '" + productdir + "'"))
        return

    product = harp.import_product(files)
    wplot(product, title="GOSAT FTS L2 CH4")


run()
