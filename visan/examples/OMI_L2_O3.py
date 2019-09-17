# This is an example VISAN script for the OMI_L2 O3 TOMS and DOAS products

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing OMI_L2 O3 TOMS or DOAS products.

# This example will then take the first product it finds in this directory and
# for that product plot the total ozone columns


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all OMI O3 files in productdir. We first try to find O3
    # TOMS files and if that fails we try to find the O3 DOAS files.
    files = glob.glob(os.path.join(productdir, "OMI-Aura_L2-OMTO3*"))
    if len(files) == 0:
        files = glob.glob(os.path.join(productdir, "OMI-Aura_L2-OMDOAO3*"))
    if len(files) == 0:
        print(("Could not find any OMTO3/OMDOAO3 files in directory '" + productdir + "'"))
        return

    # Ingest the total ozone column values from the first OMI L2 O3 file from
    # the list.
    o3 = harp.import_product(files[0])
    w = wplot(o3, colortable="Ozone", colorrange=(150.0, 500.0), numcolorlabels=8)


run()
