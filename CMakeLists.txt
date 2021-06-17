cmake_minimum_required(VERSION 3.15)

project(visan)

set(VERSION 4.1)

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


# visan python package

# We install in SITEARCH and not SITELIB because we need to bundle the package with the visanplot python module
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/visan DESTINATION ${Python3_SITEARCH})


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
  set(my_config_dir cmake/visanplot)
else()
  set(my_config_dir ${CMAKE_INSTALL_LIBDIR}/cmake/visanplot)
endif()

include(GNUInstallDirs)

#if(WIN32)
#  # all non-python components need to be installed in a Library sub-directory for Conda on Windows
#  set(BIN_PREFIX Library/bin)
#  set(LIB_PREFIX Library/lib)
#else()
#  set(BIN_PREFIX bin)
#  set(LIB_PREFIX lib)
#endif()

if(WIN32)
  set(cmake_config_dir cmake/visan)
else()
  set(cmake_config_dir ${CMAKE_INSTALL_LIBDIR}/cmake/visan)
endif()

vtk_module_find_modules(vtk_module_files ${CMAKE_CURRENT_SOURCE_DIR})

vtk_module_scan(
  MODULE_FILES        ${vtk_module_files}
  REQUEST_MODULES     VISAN::plot
  PROVIDES_MODULES    visan_vtk_modules
  ENABLE_TESTS        "${BUILD_TESTING}")

vtk_module_build(
  MODULES             ${visan_vtk_modules}
  INSTALL_EXPORT      VISAN
  CMAKE_DESTINATION   "${cmake_config_dir}"
  VERSION             "${VISAN_VERSION}"
  SOVERSION           "1")

vtk_module_wrap_python(
  MODULES             ${visan_vtk_modules}
  INSTALL_EXPORT      VISAN
  PYTHON_PACKAGE      "visan.plot"
  CMAKE_DESTINATION   "${cmake_config_dir}"
  BUILD_STATIC        OFF)


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
