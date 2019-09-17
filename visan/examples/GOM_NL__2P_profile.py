# This is an example VISAN script for the GOM_NL__2P product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing GOM_NL__2P products.

# This example will then plot the ozone profiles for all GOMOS L2 products in that directory


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir starting with 'GOM_NL__2P'
    files = glob.glob(os.path.join(productdir, "GOM_NL__2P*"))

    if len(files) == 0:
        print(("Could not find any GOM_NL__2P files in directory '" + productdir + "'"))
        return

    # We ingest the ozone profile data
    product = harp.import_product(files)

    plot(product, xlabel="value [cm-3]", showpropertypanel=True, name="o3 profile",
         title="GOM_NL__2P profile example (o3)")


run()
