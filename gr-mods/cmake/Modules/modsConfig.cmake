INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_MODS mods)

FIND_PATH(
    MODS_INCLUDE_DIRS
    NAMES mods/api.h
    HINTS $ENV{MODS_DIR}/include
        ${PC_MODS_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    MODS_LIBRARIES
    NAMES gnuradio-mods
    HINTS $ENV{MODS_DIR}/lib
        ${PC_MODS_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
)

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(MODS DEFAULT_MSG MODS_LIBRARIES MODS_INCLUDE_DIRS)
MARK_AS_ADVANCED(MODS_LIBRARIES MODS_INCLUDE_DIRS)

