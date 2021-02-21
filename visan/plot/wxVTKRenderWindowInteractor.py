# Patch for vtkmodules.wx.wxVTKRenderWindowInteractor (VTK 8.2)
# On macOS the baseclass also needs to use wx.glcanvas.GLCanvas
# otherwise rendering on hidpi screens will use the wrong resolution

import wx
if wx.Platform == "__WXMAC__":
    import wx.glcanvas
    Window = wx.Window
    wx.Window = wx.glcanvas.GLCanvas
    from vtkmodules.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
    wx.Window = Window
else:
    from vtkmodules.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
