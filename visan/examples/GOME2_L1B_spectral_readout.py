# This is an example VISAN script for the GOME-2 L1B product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing GOME-2 L1B products.

# This example will then take the first product it finds in this directory and
# for that product plot the first 100 measured spectra (for the full wavelength range)


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir starting with 'GOME_xxx_1B'
    files = glob.glob(os.path.join(productdir, "GOME_xxx_1B*"))
    if len(files) == 0:
        print(("Could not find any GOME_xxx_1B files in directory '" + productdir + "'"))
        return

    # We only ingest the first file from the list
    file = files[0]

    # Get just the geolocation information and cloud fractions (without spectra)
    # We also filter out any backward scan pixels
    geo = harp.import_product(file, 'scan_direction_type=="forward";'
                              'keep(latitude_bounds,longitude_bounds,cloud_fraction)')

    # Since the only 'value' in the geo record is the integration_time the
    # worldmap plot will use the integration_time as color values for each swath
    wplot(geo, title="Cloud fraction from GOME-2 L1B measurements", colorrange=(0, 1))

    # Get the first set of spectra (but only consider the first 200 measurements)
    product = harp.import_product(file, 'scan_direction_type=="forward";index<200')

    plot(product, name=os.path.basename(file), title="GOME-2 L1B spectral readout example")


run()
