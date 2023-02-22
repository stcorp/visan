cmake_minimum_required(VERSION 3.15)

cmake_policy(SET CMP0094 NEW)  # Find Python by LOCATION

project(visan)

set(VERSION 4.3.2)

set(CMAKE_MACOSX_RPATH ON)

if(MSVC)
  # Suppress warnings from VC on deprecated POSIX names and unsafe functions
  add_definitions(-D_CRT_NONSTDC_NO_DEPRECATE -D_CRT_SECURE_NO_WARNINGS)
endif(MSVC)

if(DEFINED ENV{CONDA_PREFIX})
  # Make sure we use the python version from the conda environment
  set(ENV{Python3_ROOT_DIR} $ENV{CONDA_PREFIX})
endif()
set(Python3_FIND_STRATEGY LOCATION)
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)


# visanplot

find_package(VTK REQUIRED COMPONENTS
  CommonCore
  CommonDataModel
  CommonExecutionModel
  CommonTransforms
  FiltersCore
  FiltersGeneral
  FiltersSources
  InteractionStyle
  RenderingAnnotation
  RenderingCore
  RenderingOpenGL2
  libproj)

get_target_property(_vtk_lib_type VTK::CommonCore TYPE)
if(_vtk_lib_type STREQUAL SHARED_LIBRARY)
  set(_default ON)
else()
  set(_default OFF)
endif()
option(BUILD_SHARED_LIBS "Build shared libraries." ${_default})

if(WIN32)
  # all non-python components need to be installed in a Library sub-directory for Conda on Windows
  set(BIN_PREFIX Library/bin)
  set(LIB_PREFIX Library/lib)
  set(DYLIB_PREFIX Library/bin)
  set(INCLUDE_PREFIX Library/include)
  set(LIBDATA_PREFIX Library)
  set(SHARE_PREFIX Library/share)
else()
  set(BIN_PREFIX bin)
  set(LIB_PREFIX lib)
  set(DYLIB_PREFIX lib)
  set(INCLUDE_PREFIX include)
  set(LIBDATA_PREFIX lib)
  set(SHARE_PREFIX share)
endif()
file(RELATIVE_PATH Python3_SITEARCH_RELATIVE "${CMAKE_INSTALL_PREFIX}" "${Python3_SITEARCH}")

vtk_module_find_modules(vtk_module_files ${CMAKE_CURRENT_SOURCE_DIR})

vtk_module_scan(
  MODULE_FILES ${vtk_module_files}
  REQUEST_MODULES VISAN::plot
  PROVIDES_MODULES visan_vtk_modules)

vtk_module_build(
  MODULES ${visan_vtk_modules}
  INSTALL_EXPORT VISAN
  ARCHIVE_DESTINATION "${LIB_PREFIX}"
  HEADERS_DESTINATION "${INCLUDE_PREFIX}/visan"
  LIBRARY_DESTINATION "${DYLIB_PREFIX}"
  RUNTIME_DESTINATION "${BIN_PREFIX}"
  CMAKE_DESTINATION "${LIBDATA_PREFIX}/cmake/visan"
  LICENSE_DESTINATION "${SHARE_PREFIX}/licenses"
  HIERARCHY_DESTINATION "${LIBDATA_PREFIX}/vtk/hierarchy/visan"
  VERSION "${VISAN_VERSION}"
  SOVERSION "1")

vtk_module_wrap_python(
  MODULES ${visan_vtk_modules}
  INSTALL_EXPORT VISAN
  PYTHON_PACKAGE "visan.plot"
  CMAKE_DESTINATION "${LIBDATA_PREFIX}/cmake/visan"
  MODULE_DESTINATION "${Python3_SITEARCH_RELATIVE}"
  STATIC_MODULE_DESTINATION "${LIB_PREFIX}"
  LIBRARY_DESTINATION "${DYLIB_PREFIX}"
  BUILD_STATIC OFF)


# visan python package

# We install in SITEARCH and not SITELIB because we need to bundle the package with the visanplot python module
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/visan DESTINATION ${Python3_SITEARCH_RELATIVE})


# visan application

if(APPLE)
  install(PROGRAMS app/macos/visan.sh DESTINATION bin RENAME visan)
  install(FILES app/macos/PkgInfo app/macos/Info.plist DESTINATION VISAN.app/Contents)
  install(FILES app/macos/visan.icns DESTINATION VISAN.app/Contents/Resources)
  install(FILES app/macos/visan DESTINATION VISAN.app/Contents/MacOS
    PERMISSIONS OWNER_WRITE OWNER_READ GROUP_READ WORLD_READ OWNER_EXECUTE GROUP_EXECUTE WORLD_EXECUTE)
  install(CODE "execute_process(COMMAND ${CMAKE_COMMAND} -E create_symlink ../../bin \$ENV{DESTDIR}\${CMAKE_INSTALL_PREFIX}/VISAN.app/Contents/bin)")
  install(CODE "execute_process(COMMAND ${CMAKE_COMMAND} -E create_symlink ../../lib \$ENV{DESTDIR}\${CMAKE_INSTALL_PREFIX}/VISAN.app/Contents/lib)")
  install(CODE "execute_process(COMMAND ${CMAKE_COMMAND} -E create_symlink ../../share \$ENV{DESTDIR}\${CMAKE_INSTALL_PREFIX}/VISAN.app/Contents/share)")
elseif(WIN32)
  add_executable(visan WIN32 app/windows/visan.c)
  install(TARGETS visan DESTINATION Scripts)
else()
  install(PROGRAMS app/visan.sh DESTINATION bin RENAME visan)
endif()
