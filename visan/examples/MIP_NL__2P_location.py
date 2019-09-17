# This is an example VISAN script for the MIP_NL__2P product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing MIP_NL__2P products.

# This example will then take all products it finds in this directory and
# for these products plot the ozone profiles and geolocation


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir starting with 'MIP_NL__2P'
    files = glob.glob(os.path.join(productdir, "MIP_NL__2P*"))

    if len(files) == 0:
        print(("Could not find any MIP_NL__2P files in directory '" + productdir + "'"))
        return

    # We ingest the ozone profile data
    # By providing a minimum value for the O3 vmr we also automatically filter out all NaN values
    data = harp.import_product(files, 'O3_volume_mixing_ratio>=0', 'species=O3')

    wplot(data, projection="Plate Caree", pointsize=3, colortable='RedToGreen')
    plot(data, showpropertypanel=True, color=(0, 1, 0), title="MIP_NL__2P profile example")


run()
