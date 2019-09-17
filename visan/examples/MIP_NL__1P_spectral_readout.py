# This is an example VISAN script for the MIP_NL__1P product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing MIP_NL__1P products.

# This example will then take the first product it finds in this directory and
# for that product plot the measured fourier spectra for band AB


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir starting with 'MIP_NL__1P'
    files = glob.glob(os.path.join(productdir, "MIP_NL__1P*"))

    if len(files) == 0:
        print(("Could not find any MIP_NL__1P files in directory '" + productdir + "'"))
        return

    # We only ingest the first file from the list
    product = harp.import_product(files[0], options="band=AB")

    plot(product, ylabel="W/(cm^2\n sr cm^-1)", showpropertypanel=True, name=os.path.basename(files[0]),
         title="MIP_NL__1P spectral readout example (band AB)")


run()
