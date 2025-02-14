#!/bin/env bash

. $ARTDAQ_DAQINTERFACE_DIR/bin/exit_if_bad_environment.sh
. $ARTDAQ_DAQINTERFACE_DIR/bin/daqinterface_functions.sh

if (($num_daqinterfaces > 0 )); then
    list_daqinterfaces
else
    echo "No instances of DAQInterface are up"
fi
