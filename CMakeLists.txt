cmake_minimum_required(VERSION 2.8)

project(visan)

set(VERSION 4.0)

set(CMAKE_MACOSX_RPATH ON)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(PythonLibs REQUIRED)


# visan python package

configure_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/setup.py.in
  ${CMAKE_CURRENT_BINARY_DIR}/setup.py)

install(CODE "execute_process(COMMAND ${Python3_EXECUTABLE} setup.py install --root=/ --prefix=\$ENV{DESTDIR}\${CMAKE_INSTALL_PREFIX} --single-version-externally-managed)")


# visanplot

add_subdirectory(visanplot)


# VISAN.app (mac only)

if(APPLE)
  install(FILES macos/PkgInfo macos/Info.plist DESTINATION VISAN.app/Contents)
  install(FILES macos/visan.icns DESTINATION VISAN.app/Contents/Resources)
  install(FILES macos/visan DESTINATION VISAN.app/Contents/MacOS
    PERMISSIONS OWNER_WRITE OWNER_READ GROUP_READ WORLD_READ OWNER_EXECUTE GROUP_EXECUTE WORLD_EXECUTE)
  install(CODE "execute_process(COMMAND ${CMAKE_COMMAND} -E create_symlink ../../bin \$ENV{DESTDIR}\${CMAKE_INSTALL_PREFIX}/VISAN.app/Contents/bin)")
  install(CODE "execute_process(COMMAND ${CMAKE_COMMAND} -E create_symlink ../../lib \$ENV{DESTDIR}\${CMAKE_INSTALL_PREFIX}/VISAN.app/Contents/lib)")
  install(CODE "execute_process(COMMAND ${CMAKE_COMMAND} -E create_symlink ../../share \$ENV{DESTDIR}\${CMAKE_INSTALL_PREFIX}/VISAN.app/Contents/share)")
endif()
