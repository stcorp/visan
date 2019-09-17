# This is an example VISAN script for the SCI_OL__2P product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing SCI_OL__2P products.

# This example will then take all products it finds in this directory and
# for these products plot the ozone profiles from the limb mode


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir starting with 'SCI_OL__2P'
    files = glob.glob(os.path.join(productdir, "SCI_OL__2P*"))
    if len(files) == 0:
        print(("Could not find any SCI_OL__2P files in directory '" + productdir + "'"))
        return

    # We ingest the ozone profile data that was retrieved using UV/VIS fitting window no. 0.
    o3 = harp.import_product(files, "", "dataset=lim_uv0_o3")

    wplot(o3, projection="Plate Caree", pointsize=3, colortable='RedToGreen')
    window = plot(o3, title="SCI_OL__2P profile example (o3)")


run()
