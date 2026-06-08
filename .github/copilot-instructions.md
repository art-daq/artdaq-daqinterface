# Project Overview

This project is a collection of tools and utilities for the artdaq framework, which is used for data acquisition in high-energy physics experiments. The repository includes code for data processing, monitoring, and analysis, as well as documentation and examples to help users get started with artdaq.

## Folder Structure

- `./artdaq`: Contains the main codebase for the artdaq framework, including core libraries and utilities.
- `./doc`: Doxygen documentation hook for CMake
- `./proto`: Executables using the artdaq framework
- `./test`: Boost Unit tests
- `./tools`: Scripts and utilities

## Libraries and Frameworks

artdaq is built on the art framework, which provides a modular and flexible architecture for data processing. It also utilizes various C++ libraries for tasks such as serialization, logging, and configuration management.

artdaq is built using CMake and the Spack package manager. A build environment is provided in the `ghcr.io/art-daq/artdaq-spack` Docker image, which includes all necessary dependencies and tools for building and running artdaq. The build environment is located at /opt/artdaq within the container.

## Coding Standards

All C++ source files must be formatted with `clang-format`. C/C++ header files should be formatted with `clang-format` using the `.clang-format-hpp` instruction file if it exists, `.clang-format` otherwise. All python files must be formatted with `black`. The project uses the Google C++ Style Guide as a reference for coding standards, with some modifications to fit the specific needs of the artdaq framework. Developers are encouraged to follow these guidelines to maintain consistency and readability across the codebase.

## Agent Instructions

When using GitHub Copilot, please ensure that the generated code adheres to the project's coding standards and guidelines. Review the generated code carefully and make any necessary adjustments to ensure it fits well within the existing codebase. Additionally, consider the context of the code being generated and how it interacts with other parts of the project to maintain overall coherence and functionality. Keep changes to a minimum, prefer removing older code and replacing with new and more efficient code. Use modern C++ standards. Be critical of existing code and suggest improvements where possible. Always prioritize readability and maintainability in the generated code.
