# This is an example VISAN script for the MIP_NL__2P product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing MIP_NL__2P products.

# This example will then take all products it finds in this directory and
# for these products plot the ozone profiles


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir starting with 'MIP_NL__2P'
    files = glob.glob(os.path.join(productdir, "MIP_NL__2P*"))
    if len(files) == 0:
        print(("Could not find any MIP_NL__2P files in directory '" + productdir + "'"))
        return

    # When we exclude altitude (but still include pressure), the plot command will use pressure for the y-axis
    # By providing a minimum value for the O3 vmr we also automatically filter out all NaN values
    o3 = harp.import_product(files[0], "exclude(altitude);O3_volume_mixing_ratio>=0", "species=O3")

    window = plot(o3, ylabel="p [hPa]", xmin=0, title="MIP_NL__2P profile example (o3)")


run()
