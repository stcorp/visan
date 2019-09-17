# This is an example VISAN script for the ALD_U_N_1B product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing ALD_U_N_1B products.

# This example will then take the first product it finds in this directory and
# for this product plot the Mie and Rayleigh wind profiles for measurements and observations


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all DBL files in productdir containing with 'ALD_U_N_1B'
    files = glob.glob(os.path.join(productdir, "*ALD_U_N_1B*.DBL"))
    if len(files) == 0:
        print(("Could not find any ALD_U_N_1B files in directory '" + productdir + "'"))
        return

    # We only take the first file
    filename = files[0]

    # Since the L1b data only has altitude boundaries we need to perform a
    # derive(altitude {time,vertical} [km]) to get the center altitude values for plotting
    operations = "derive(altitude {time,vertical} [km])"
    # We also turn the lat/lon values per profile point to single lat/lon values per profile
    # This allows us to show the location of each profile in the plot property panel
    operations += ";derive(latitude {time});derive(longitude {time})"

    # Rayleigh Observations (default)
    data = harp.import_product(filename, operations)
    plot(data, title="ALD_U_N_1B Rayleight Observations", xrange=[-500, 500])

    # Mie Observations
    data = harp.import_product(filename, operations, "data=mie_observation")
    plot(data, title="ALD_U_N_1B Mie Observations", xrange=[-500, 500])

    # Rayleigh Measuruments
    data = harp.import_product(filename, operations, "data=rayleigh_measurement")
    plot(data, title="ALD_U_N_1B Rayleight Measuruments", xrange=[-500, 500])

    # Mie Measurements
    data = harp.import_product(filename, operations, "data=mie_measurement")
    plot(data, title="ALD_U_N_1B Mie Measuruments", xrange=[-500, 500])


run()
