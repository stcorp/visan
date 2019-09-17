# This is an example VISAN script for the SCI_NL__1P product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing SCI_NL__1P products.

# This example will then take the first product it finds in this directory and
# for that product plot the measured limb spectra for the range 290nm - 450nm


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir starting with 'SCI_NL__1P' and ending with '.child'
    files = glob.glob(os.path.join(productdir, "SCI_NL__1P*.child"))

    if len(files) == 0:
        print(("Could not find any SCI_NLC_1P files in directory '" + productdir + "'"))
        return

    # We only ingest the first file from the list
    record = harp.import_product(files[0], "wavelength>=290;wavelength<=450", "data=limb")

    plot(record, showpropertypanel=True, name=os.path.basename(files[0]),
         title="SCI_NLC_1P spectral readout example (limb: 290-450nm)")
    wplot(record, colortable='RedToGreen', projection="Mollweide")


run()
