# This is an example VISAN script to create a daily grid of S5P NO2 L2 product data

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing one day of S5P NO2 L2 products.

# This example will then take all products it finds in this directory
# create a global grid from it and plot the resulting daily grid of tropospheric NO2 columns


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all S5P NO2 files in productdir
    files = glob.glob(os.path.join(productdir, "S5P_????_L2__NO2*"))

    if len(files) == 0:
        print(("Could not find any S5P NO2 L2 files in directory '" + productdir + "'"))
        return

    # Filter for quality, turn each product into a lat/lon grid and merge these grids into a single daily grid
    data = harp.import_product(files, 'tropospheric_NO2_column_number_density_validity>75;keep(datetime_start,datetime_length,latitude_bounds,longitude_bounds,tropospheric_NO2_column_number_density);bin_spatial(1801,-90,0.1,3601,-180,0.1);derive(latitude {latitude});derive(longitude {longitude});exclude(latitude_bounds,longitude_bounds)', post_operations='bin();squash(time, (latitude,longitude));derive(tropospheric_NO2_column_number_density [Pmolec/cm2])')

    wplot(data, value="tropospheric_NO2_column_number_density", colorrange=(0,20), showpropertypanel=True)


run()
