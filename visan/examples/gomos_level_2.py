# This is an example VISAN script for GOMOS L2 products using CODA

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing GOM_NL__2P products.

# This example will then take the first product it finds in this directory and
# for that product plot the ozone profile


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all GOMOS L2 files in productdir.
    files = glob.glob(os.path.join(productdir, "GOM_NL__2P*"))
    if len(files) == 0:
        print(("Could not find any GOM_NL__2P files in directory '" + productdir + "'"))
        return

    # Ingest the ozone profile and tangent altitudes from the first GOMOS L2
    # product file.

    pf = coda.open(files[0])
    tangent_alt = coda.fetch(pf, 'nl_geolocation', -1, 'tangent_alt')
    o3 = coda.fetch(pf, 'nl_local_species_density', -1, 'o3')

    # convert altitude to km
    tangent_alt /= 1000

    # plot height vs. O3
    plot(o3, tangent_alt, title="GOMOS Level-2: Ozone profile", xlabel="Local O3 density at tangent height [ cm^-3 ]",
         ylabel="height\n[ km ]", yrange=(0, 75))

    coda.close(pf)


run()
