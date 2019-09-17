# This is an example VISAN script for the GOSAT CAI L2 CLD product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing GOSAT CAI L2 CLD products.

# This example will then take the first product it finds in this directory and
# for that product plot the cloud flag


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all GOSAT CAI L2 CLDM files in productdir
    files = glob.glob(os.path.join(productdir, "GOSATTCAI*02CLDM*"))
    if len(files) == 0:
        print(("Could not find any GOSAT CAI L2 CLDM files in directory '" + productdir + "'"))
        return

    # use only the first file
    pf = coda.open(files[0])
    cloudflag = coda.fetch(pf, 'Data', 'cloudFlag', 'cloudFlag')
    latitude = coda.fetch(pf, 'Data', 'geolocation', 'latitude')
    longitude = coda.fetch(pf, 'Data', 'geolocation', 'longitude')

    # filter out all invalid values
    latitude = latitude[cloudflag != -9999]
    longitude = longitude[cloudflag != -9999]
    cloudflag = cloudflag[cloudflag != -9999]

    wplot(latitude, longitude, cloudflag, title="GOSAT CAI L2 Cloud Flag")


run()
