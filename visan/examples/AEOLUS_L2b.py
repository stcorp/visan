# This is an example VISAN script for the ALD_U_N_2B product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing ALD_U_N_2B products.

# This example will then take the first product it finds in this directory and
# for this product plot the Mie and Rayleigh wind profiles for measurements and observations


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all DBL files in productdir containing with 'ALD_U_N_2B'
    files = glob.glob(os.path.join(productdir, "*ALD_U_N_2B*.DBL"))
    if len(files) == 0:
        print(("Could not find any ALD_U_N_2B files in directory '" + productdir + "'"))
        return

    # We only take the first file
    filename = files[0]

    # Rayleigh (default)
    data = harp.import_product(filename)
    plot(data, title="ALD_U_N_2B Rayleigh Observations", xrange=[-5e4, 5e4])

    # Mie
    data = harp.import_product(filename, "", "data=mie")
    plot(data, title="ALD_U_N_2B Mie Observations", xrange=[-5e4, 5e4])

    # Rayleigh, but only the valid measurements (as a plain list of points)
    data = harp.import_product(filename, "flatten(vertical);hlos_wind_velocity_validity==1")
    plot(data.latitude.data, data.hlos_wind_velocity.data, points=1, lines=0, pointsize=0.1, xlabel="latitude", ylabel=data.hlos_wind_velocity.unit, title="ALD_U_N_2B Rayleigh Observations (points)")

    # Mie, but only the valid measurements (as a plain list of points)
    data = harp.import_product(filename, "flatten(vertical);hlos_wind_velocity_validity==1", "data=mie")
    plot(data.latitude.data, data.hlos_wind_velocity.data, points=1, lines=0, pointsize=0.1, xlabel="latitude", ylabel=data.hlos_wind_velocity.unit, title="ALD_U_N_2B Mie Observations (points)")


run()
