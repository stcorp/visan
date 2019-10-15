# This is an example VISAN script for the S5P NO2 L2 product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing S5P NO2 L2 products.

# This example will then take the first product it finds in this directory and
# plot the tropospheric NO2 column


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all S5P NO2 files in productdir
    files = glob.glob(os.path.join(productdir, "S5P_????_L2__NO2*"))

    if len(files) == 0:
        print(("Could not find any S5P NO2 L2 files in directory '" + productdir + "'"))
        return

    # Filter for quality and convert NO2 column number denstiy to Pmolec/cm2 as part of ingestion
    data = harp.import_product(files[0], 'tropospheric_NO2_column_number_density_validity>75;derive(tropospheric_NO2_column_number_density [Pmolec/cm2])')

    wplot(data, value="tropospheric_NO2_column_number_density", colorrange=(0,20), showpropertypanel=True)


run()
