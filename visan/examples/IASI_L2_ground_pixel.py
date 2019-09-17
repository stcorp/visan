# This is an example VISAN script for the IASI L2 (IASI_SND_02) product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing IASI_SND_02 products.

# This example will then take the first product it finds in this directory and
# for that product plot the total ozone columns


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir starting with 'IASI_SND_02'
    files = glob.glob(os.path.join(productdir, "IASI_SND_02*"))

    if len(files) == 0:
        print(("Could not find any IASI_SND_02 files in directory '" + productdir + "'"))
        return

    # since the IASI files can be quite big, we just ingest data from the first file
    product = harp.import_product(files[0])

    wplot(product, title="IASI Level 2")


run()
