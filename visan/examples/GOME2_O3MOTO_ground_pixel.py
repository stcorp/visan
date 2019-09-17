# This is an example VISAN script for the GOME-2 O3MOTO product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing GOME-2 O3MOTO products (in HDF5 format).

# This example will then take all products it finds in this directory and
# for these products plot the total ozone columns


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir starting with 'GOME_*_L2_*.HDF5'
    files = glob.glob(os.path.join(productdir, "GOME_*_L2_*.HDF5"))

    if len(files) == 0:
        print(("Could not find any GOME2 L2 files in directory '" + productdir + "'"))
        return

    # All backward scans are left out of the ingestion.
    product = harp.import_product(files, 'scan_direction_type=="forward"')

    wplot(product, value="O3_column_number_density", colorrange=(150, 500), numcolorlabels=8, colortable="Ozone",
          showpropertypanel=True)


run()
