# This is an example VISAN script showing the extraction and plotting of ECMWF MARS data in GRIB format

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel
# to a directory containing ECMWF MARS GRIB products.

# This example will then take the first product it finds in this directory and
# for that product plot the O3 column number density


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir starting with 'C1D'
    files = glob.glob(os.path.join(productdir, "*.grib"))
    if len(files) == 0:
        print(("Could not find any GRIB files in directory '" + productdir + "'"))
        return

    # We only take the first file
    filename = files[0]

    # O3 is by default provided as mass column densities
    # During import we derive a new variable from this that contains a column number density with unit DU
    # And at the end we remove the mass column density variable again since we don't need it anymore
    data = harp.import_product(filename, "keep(latitude,longitude,O3_column_density);"
                               "derive(O3_column_number_density {latitude,longitude} [DU]);exclude(O3_column_density)")
    wplot(data, colorrange=[150, 500])


run()
