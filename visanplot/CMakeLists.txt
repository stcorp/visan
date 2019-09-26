cmake_minimum_required(VERSION 2.8)

project(visanplot)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

find_package(VTK REQUIRED COMPONENTS
  vtkCommonCore
  vtkCommonDataModel
  vtkCommonExecutionModel
  vtkCommonTransforms
  vtkFiltersCore
  vtkFiltersGeneral
  vtkFiltersSources
  vtkInteractionStyle
  vtkRenderingAnnotation
  vtkRenderingCore
  vtkRenderingOpenGL2
  vtklibproj)
include(${VTK_USE_FILE})

if (UNIX AND NOT APPLE)
  find_package(OpenGL)
endif()

include(vtkWrapPython)
include(vtkWrapHierarchy)
include(vtkTargetLinkLibrariesWithDynamicLookup)

include_directories("${CMAKE_CURRENT_SOURCE_DIR}" "${Python3_INCLUDE_DIRS}" "${VTK_INCLUDE_DIRS}")

if(WIN32)
  # all non-python components need to be installed in a Library sub-directory for Conda on Windows
  set(BIN_PREFIX Library/bin)
  set(LIB_PREFIX Library/lib)
else()
  set(BIN_PREFIX bin)
  set(LIB_PREFIX lib)
endif()

set(visanplot_SOURCES
  vtkCoastLineData
  vtkColorTable
  vtkGSHHSReader
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

add_library(visanplot SHARED ${visanplot_SOURCES})
target_link_libraries(visanplot ${VTK_LIBRARIES})
if (UNIX AND NOT APPLE)
  target_link_libraries(visanplot ${OPENGL_LIBRARIES})
endif()

set(visanplot_WRAP_DEPENDS vtkCommonCore vtkFiltersCore vtkRenderingAnnotation vtkRenderingCore)
vtk_wrap_hierarchy(visanplot ${CMAKE_CURRENT_BINARY_DIR} "${visanplot_SOURCES}")
set(KIT_HIERARCHY_FILE ${CMAKE_CURRENT_BINARY_DIR}/visanplotHierarchy.txt)
vtk_wrap_python3(visanplotPython visanplotPython_SOURCES "${visanplot_SOURCES}")

add_library(visanplotPythonD ${visanplotPython_SOURCES} ${visanplot_SOURCES})
set_property(TARGET visanplotPythonD PROPERTY POSITION_INDEPENDENT_CODE ON)
target_link_libraries(visanplotPythonD ${VTK_LIBRARIES} vtkWrappingPythonCore)

set(VTK_MODULES_USED vtkRenderingCore)
set(VTK_PYTHOND_LIBS)
foreach(TMP_LIB ${VTK_MODULES_USED})
  set(VTK_PYTHOND_LIBS ${VTK_PYTHOND_LIBS} ${TMP_LIB}PythonD)
endforeach()

add_library(visanplotPython MODULE visanplotPythonInit.cxx)
set_property(TARGET visanplotPython PROPERTY PREFIX "")
if(WIN32)
  set_property(TARGET visanplotPython PROPERTY SUFFIX ".pyd")
endif()
target_link_libraries(visanplotPython PUBLIC visanplotPythonD ${VTK_PYTHOND_LIBS})
vtk_target_link_libraries_with_dynamic_lookup(visanplotPython LINK_PUBLIC ${Python3_LIBRARIES})

if(WIN32)
  install(TARGETS visanplot DESTINATION ${LIB_PREFIX})
else(WIN32)
  install(TARGETS visanplot RUNTIME DESTINATION ${BIN_PREFIX} ARCHIVE DESTINATION ${LIB_PREFIX})
endif(WIN32)
install(TARGETS visanplotPython DESTINATION ${Python3_SITEARCH}/visan/plot)

# Demo applications (not installed)
add_executable(worldplotdemo MACOSX_BUNDLE worldplotdemo.cxx)
set_target_properties(worldplotdemo PROPERTIES COMPILE_FLAGS "-DGSHHS_FILEPATH=\\\"${CMAKE_CURRENT_SOURCE_DIR}/../visan/data/gshhs_i.b\\\"")
target_link_libraries(worldplotdemo PRIVATE visanplot ${VTK_LIBRARIES})

add_executable(plotdemo MACOSX_BUNDLE plotdemo.cxx)
target_link_libraries(plotdemo PRIVATE visanplot ${VTK_LIBRARIES})
