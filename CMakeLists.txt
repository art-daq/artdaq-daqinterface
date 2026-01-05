# ======================================================================
#  artdaq-daqinterface main build file
#
#  cd .../path/to/build/directory
#  source .../path/to/artdaq-utilities/ups/setup_for_development
#  cmake [-DCMAKE_INSTALL_PREFIX=/install/path]
#        -Dqualifier:STRING=$CETPKG_QUAL
#        -DCMAKE_BUILD_TYPE=$CETPKG_TYPE
#        $CETPKG_SOURCE
#  make
#  make test
#  make install
#  make package
# ======================================================================

# use cmake 2.8 or later
cmake_minimum_required (VERSION 3.16)

find_package(cetmodules)

project(artdaq-daqinterface VERSION 4.03.01)

set(artdaq_daqinterface_NOARCH TRUE)

include(CetCMakeEnv)
cet_cmake_env()
SET(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

cet_set_compiler_flags(DIAGS VIGILANT
  WERROR
  NO_UNDEFINED
  EXTRA_FLAGS -pedantic
)

#cet_report_compiler_flags()

INSTALL(DIRECTORY bin DESTINATION . FILE_PERMISSIONS USE_SOURCE_PERMISSIONS)
INSTALL(DIRECTORY docs DESTINATION . FILE_PERMISSIONS USE_SOURCE_PERMISSIONS)
INSTALL(DIRECTORY rc DESTINATION . FILE_PERMISSIONS USE_SOURCE_PERMISSIONS)
INSTALL(DIRECTORY simple_test_config DESTINATION . FILE_PERMISSIONS USE_SOURCE_PERMISSIONS)
INSTALL(DIRECTORY utils DESTINATION . FILE_PERMISSIONS USE_SOURCE_PERMISSIONS)
INSTALL(FILES source_me DESTINATION .)

cet_cmake_config()
