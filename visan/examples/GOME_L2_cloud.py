# This is an example VISAN script for the GOME_L2 product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing GOME L2 products (using ERS binary format).

# This example will then take all L2 products it finds in this directory and
# for these products plot the ozone total columns, overplotted with cloud fractions


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir ending with '.lv2'
    files = glob.glob(os.path.join(productdir, "*.lv2"))
    if len(files) == 0:
        print(("Could not find any GOME_L2 files in directory '" + productdir + "'"))
        return

    # Ingest the total ozone column values and the cloud fraction,
    # but ingest only the forward scan pixels and make sure that O3 is in Dobson Units
    data = harp.import_product(files, 'scan_direction_type=="forward";derive(O3_column_number_density [DU])')
    print(data)
    w = wplot(data, colortable="Ozone", colorrange=(150.0, 500.0), numcolorlabels=8)
    wplot(data, value="cloud_fraction", colortable="Cloud", colorrange=(0.0, 1.0), numcolorlabels=5, deltaradius=0.02,
          window=w)
    w.SetPlotTitle('Ozone with cloud cover overlay')


run()
