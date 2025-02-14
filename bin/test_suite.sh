#!/bin/env bash

# JCF, Feb-3-2017

# Be aware that:

# This script was originally tested (i.e., tested to see that it
# performs tests correctly) using artdaq-demo v2_08_04

# This script expects simple_test_config/demo/component01.fcl to exist

# This script expects the variables "change_after_N_seconds",
# "nADCcounts_after_N_seconds", "exit_after_N_seconds",
# "abort_after_N_seconds" and "exception_after_N_seconds" to exist in
# the above file

# This script will modify simple_test_config/demo/component01.fcl

standard_test=true
boardreader_hangs_test=true
process_killed_test=true
boardreader_aborts_test=true
boardreader_exits_test=true
boardreader_throws_test=true

. $ARTDAQ_DAQINTERFACE_DIR/bin/exit_if_bad_environment.sh

if [[ ! -e bin/just_do_it.sh ]]; then
    echo "Can't find bin/just_do_it.sh; are you in the base directory of artdaq-utilities-daqinterface?" >&2
    exit 10
fi

logfile=/tmp/daqinterface/DI.log
cmd="tee -a $logfile"

res=$(ps aux | grep "$cmd" | grep -v grep )

if [[ -z $res ]]; then
    echo "Failed to see a running instance of \"$cmd\" needed to save DAQInterface output; exiting..." >&2
    exit 20
fi

# Make sure this isn't a shorter time period than when the ToySimulator's pathologies are timed to kick in
runtime=10


boardreader_fhicl=simple_test_config/demo/component01.fcl

for needed_variable in change_after_N_seconds nADCcounts_after_N_seconds abort_after_N_seconds exit_after_N_seconds exception_after_N_seconds ; do

    if [[ -z $( grep -l $needed_variable $boardreader_fhicl ) ]]; then
	echo "Unable to find needed variable \"$needed_variable\" in ${boardreader_fhicl}; exiting..." >&2
	exit 40
    fi
done


if $standard_test; then

    echo $(date) "WILL TRY REGULAR RUNNING FOR $runtime SECONDS "

    sed -r -i 's/.*change_after_N_seconds.*/#change_after_N_seconds: 5/' $boardreader_fhicl
    sed -r -i 's/.*nADCcounts_after_N_seconds.*/#nADCcounts_after_N_seconds: -1/' $boardreader_fhicl
    sed -r -i 's/.*abort_after_N_seconds.*/#abort_after_N_seconds: true/' $boardreader_fhicl
    sed -r -i 's/.*exit_after_N_seconds.*/#exit_after_N_seconds: true/' $boardreader_fhicl
    sed -r -i 's/.*exception_after_N_seconds.*/#exception_after_N_seconds: true/' $boardreader_fhicl

    ./bin/just_do_it.sh $runtime

    if [[ "$?" != "0" ]]; then
	echo "just_do_it.sh RETURNED NONZERO FOR REGULAR RUNNING; SKIPPING FURTHER TESTS" >&2
	exit 30
    fi
fi

if $boardreader_hangs_test; then

    echo $(date) "WILL TRY SIMULATING A HANG FROM ONE OF THE BOARDREADERS"

    sed -r -i 's/.*change_after_N_seconds.*/change_after_N_seconds: 5/' $boardreader_fhicl
    sed -r -i 's/.*nADCcounts_after_N_seconds.*/nADCcounts_after_N_seconds: -1/' $boardreader_fhicl
    sed -r -i 's/.*abort_after_N_seconds.*/#abort_after_N_seconds: true/' $boardreader_fhicl
    sed -r -i 's/.*exit_after_N_seconds.*/#exit_after_N_seconds: true/' $boardreader_fhicl
    sed -r -i 's/.*exception_after_N_seconds.*/#exception_after_N_seconds: true/' $boardreader_fhicl

    ./bin/just_do_it.sh $runtime

fi

if $process_killed_test; then

    echo $(date) "WILL RUN INDEFINITELY - THIS GIVES YOU AN OPPORTUNITY TO EXTERNALLY KILL AN ARTDAQ PROCESS TO SEE WHAT HAPPENS"

    sed -r -i 's/.*change_after_N_seconds.*/#change_after_N_seconds: 5/' $boardreader_fhicl
    sed -r -i 's/.*nADCcounts_after_N_seconds.*/#nADCcounts_after_N_seconds: -1/' $boardreader_fhicl
    sed -r -i 's/.*abort_after_N_seconds.*/#abort_after_N_seconds: true/' $boardreader_fhicl
    sed -r -i 's/.*exit_after_N_seconds.*/#exit_after_N_seconds: true/' $boardreader_fhicl
    sed -r -i 's/.*exception_after_N_seconds.*/#exception_after_N_seconds: true/' $boardreader_fhicl

    ./bin/just_do_it.sh 0

fi

if $boardreader_aborts_test; then

    echo $(date) "WILL REQUEST THAT TOYSIMULATOR CALL STD::ABORT"

    sed -r -i 's/.*change_after_N_seconds.*/change_after_N_seconds: 5/' $boardreader_fhicl
    sed -r -i 's/.*nADCcounts_after_N_seconds.*/#nADCcounts_after_N_seconds: -1/' $boardreader_fhicl
    sed -r -i 's/.*abort_after_N_seconds.*/abort_after_N_seconds: true/' $boardreader_fhicl
    sed -r -i 's/.*exit_after_N_seconds.*/#exit_after_N_seconds: true/' $boardreader_fhicl
    sed -r -i 's/.*exception_after_N_seconds.*/#exception_after_N_seconds: true/' $boardreader_fhicl

    ./bin/just_do_it.sh 0
fi

if $boardreader_exits_test; then

    echo $(date) "WILL REQUEST THAT TOYSIMULATOR CALL STD::EXIT"

    sed -r -i 's/.*change_after_N_seconds.*/change_after_N_seconds: 5/' $boardreader_fhicl
    sed -r -i 's/.*nADCcounts_after_N_seconds.*/#nADCcounts_after_N_seconds: -1/' $boardreader_fhicl
    sed -r -i 's/.*abort_after_N_seconds.*/#abort_after_N_seconds: true/' $boardreader_fhicl
    sed -r -i 's/.*exit_after_N_seconds.*/exit_after_N_seconds: true/' $boardreader_fhicl
    sed -r -i 's/.*exception_after_N_seconds.*/#exception_after_N_seconds: true/' $boardreader_fhicl

    ./bin/just_do_it.sh 0
fi


if $boardreader_throws_test; then

    echo $(date) "WILL REQUEST THAT TOYSIMULATOR THROWS AN EXCEPTION"

    sed -r -i 's/.*change_after_N_seconds.*/change_after_N_seconds: 5/' $boardreader_fhicl
    sed -r -i 's/.*nADCcounts_after_N_seconds.*/#nADCcounts_after_N_seconds: -1/' $boardreader_fhicl
    sed -r -i 's/.*abort_after_N_seconds.*/#abort_after_N_seconds: true/' $boardreader_fhicl
    sed -r -i 's/.*exit_after_N_seconds.*/#exit_after_N_seconds: true/' $boardreader_fhicl
    sed -r -i 's/.*exception_after_N_seconds.*/exception_after_N_seconds: true/' $boardreader_fhicl

    ./bin/just_do_it.sh 0
fi


exit 0
