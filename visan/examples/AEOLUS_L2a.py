# This is an example VISAN script for the ALD_U_N_2A product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing ALD_U_N_2A products.

# This example will then take the first product it finds in this directory and
# for this product plot the Mie and Rayleigh wind profiles for measurements and observations


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all DBL files in productdir containing with 'ALD_U_N_2A'
    files = glob.glob(os.path.join(productdir, "*ALD_U_N_2A*.DBL"))
    if len(files) == 0:
        print(("Could not find any ALD_U_N_2A files in directory '" + productdir + "'"))
        return

    # We only take the first file
    filename = files[0]

    # We turn the lat/lon values per profile point to single lat/lon values per profile
    # This allows us to show the location of each profile in the plot property panel
    operations = "derive(latitude {time});derive(longitude {time})"
    # The validity flag is the same for each quantity, so we just use the one
    # for the extinction coefficient to filter out the levels where no
    # quantity is available (i.e. where the validity flag equals 0)
    operations += ";extinction_coefficient_validity!=0"

    data = harp.import_product(filename, operations)
    plot(data, title="ALD_U_N_2A extinction coefficient")
    plot(data, title="ALD_U_N_2A backscatter coefficient", value="backscatter_coefficient")
    plot(data, title="ALD_U_N_2A optical depth", value="optical_depth")


run()
