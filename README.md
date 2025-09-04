# artdaq-daqinterface Front Page

## About the framework

The _artdaq_ toolkit is a data-acquisition framework designed for high-energy physics experiments. It provides a flexible, reliable backbone for data transfers and has several locations where users can perform custom analysis tasks using the _art_ framework.

The _artdaq_ suite consists of the following packages:

* [trace](https://art-daq.github.io/artdaq_doxygen/trace): High-performance message logging
* [artdaq-core](https://art-daq.github.io/artdaq_doxygen/artdaq-core): Data formats used by the artdaq toolkit
* [artdaq-utilities](https://art-daq.github.io/artdaq_doxygen/artdaq-utilities): Online tools, primarily metrics reporting
* [artdaq-mfextensions](https://art-daq.github.io/artdaq_doxygen/artdaq-mfextensions): Extensions to the MessageFacility product which are useful in DAQ context
* [artdaq](https://art-daq.github.io/artdaq_doxygen/artdaq): Application and data transfer framework
* [artdaq-core-demo](https://art-daq.github.io/artdaq_doxygen/artdaq-core-demo): Data formats used by the artdaq demonstration system
* [artdaq-demo](https://art-daq.github.io/artdaq_doxygen/artdaq-demo): "User" implementations for the artdaq demonstration system
* [artdaq-daqinterface](https://art-daq.github.io/artdaq_doxygen/artdaq-daqinterface): Command line run control and example configurations
* [artdaq-database](https://art-daq.github.io/artdaq_doxygen/artdaq-database): Bindings for MongoDB or local "filesystemdb" configuration databases
* [artdaq-epics-plugin](https://art-daq.github.io/artdaq_doxygen/artdaq-epics-plugin): Metric endpoint for the EPICS control system

## About this package

This package is a Python-based run control implementation for _artdaq_, performing automatic system configuration and bookkeeping tasks. It also serves as the repository for the _artdaq-demo_ example configurations which are used as the _artdaq_ framework's regression test suite.
