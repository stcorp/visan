set(classes
  vtkColorTable
  vtkGSHHGReader
  vtkGeographyLineData
  vtkGeoGridData
  vtkGeoGridSource
  vtkGeoMapFilter
  vtkInteractorStylePlot
  vtkInteractorStyleWorldPlot2D
  vtkInteractorStyleWorldPlot3D
  vtkNewAxisActor2D
  vtkPlotActor
  vtkPlotData
  vtkPlotDataCollection
  vtkProjFilter
  vtkWorldPlotData
  vtkWorldPlotGridData
  vtkWorldPlotLineData
  vtkWorldPlotPointData
  vtkWorldPlotSwathData
  vtkXYPlotData)

vtk_module_add_module(VISAN::plot CLASSES ${classes})

# Demo applications (not installed)
add_executable(worldplotdemo MACOSX_BUNDLE worldplotdemo.cxx)
set_target_properties(worldplotdemo PROPERTIES COMPILE_DEFINITIONS "GSHHS_FILEPATH=\"${CMAKE_CURRENT_SOURCE_DIR}/../visan/data/gshhs_i.b\";WDB_BORDERS_FILEPATH=\"${CMAKE_CURRENT_SOURCE_DIR}/../visan/data/wdb_borders_i.b\"")
target_link_libraries(worldplotdemo PRIVATE VISAN::plot)

add_executable(plotdemo MACOSX_BUNDLE plotdemo.cxx)
target_link_libraries(plotdemo PRIVATE VISAN::plot)
