# This is an example VISAN script for the SCI_OL__2P product

# Make sure to set the 'products-file directory' option in the VISAN Preferences panel to
# a directory containing SCI_OL__2P products.

# This example will then take all products it finds in this directory and
# for these products plot the total ozone columns from the nadir mode


def run():

    import glob
    import wx

    productdir = str(wx.Config.Get().Read('DirectoryLocation/Products'))

    # Use glob to find all files in productdir starting with 'SCI_OL__2P'
    files = glob.glob(os.path.join(productdir, "SCI_OL__2P*"))

    if len(files) == 0:
        print(("Could not find any SCI_OL__2P files in directory '" + productdir + "'"))
        return

    # We ingest the ozone data that was retrieved using UV/VIS fitting window no. 0.
    # All backward scans are left out of the ingestion.
    # Finally we have the ingestion routine convert the VCD values to Dobson Units.
    data = harp.import_product(files, 'scan_direction_type!="backward";derive(O3_column_number_density [DU])',
                               'dataset=nad_uv0_o3')

    wplot(data, value="O3_column_number_density", colorrange=(150, 500), numcolorlabels=8, colortable="Ozone",
          showpropertypanel=True)


run()
