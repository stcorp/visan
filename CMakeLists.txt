cmake_minimum_required(VERSION 2.8)

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
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# visan python package

# We install in SITEARCH and not SITELIB because we need to bundle the package with the visanplot python module
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/visan DESTINATION ${Python3_SITEARCH})

# visanplot

add_subdirectory(visanplot)

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
