#!/bin/env bash

if [[ "$#" != 2 && "$#" != 3 ]]; then
    echo "Usage: "$( basename $0 )" <existing run number> <seconds to run> [optional argument \"--nostrict\"]"
    exit 0
fi

runnum=$1
seconds_to_run=$2

nostrict=false

if [[ -n $3 && $3 =~ nostrict ]]; then
    nostrict=true
fi

if ! [[ "$runnum" =~ ^[0-9]+$ ]] ; then
    echo "Run number argument \"$runnum\" does not appear to be an integer; exiting..." >&2
    exit 1
fi

if ! [[ "$seconds_to_run" =~ ^[0-9]+$ ]] ; then
    echo "seconds-to-run argument \"$seconds_to_run\" does not appear to be an integer; exiting..." >&2
    exit 1
fi

. $ARTDAQ_DAQINTERFACE_DIR/bin/exit_if_bad_environment.sh
. $ARTDAQ_DAQINTERFACE_DIR/bin/diagnostic_tools.sh

if $nostrict ; then

    cat<<EOF

The "--nostrict" option has been requested; will ignore the following:

-Potential differences in the code used for run $runnum and the run about to be performed
-Potential differences in the known boardreaders list used for run $runnum and the run about to be performed
-A potential difference between the host DAQInterface was on for run $runnum and the host you're currently on

EOF
fi

echo
if [[ -d $recorddir ]]; then
    echo "Will look in record directory \"$recorddir\" for run $runnum"
else
    echo "Unable to find expected record directory \"$recorddir\", exiting..." >&2
    exit 1
fi

if [[ ! -d $recorddir/$runnum ]]; then
    echo "Unable to find subdirectory \"$runnum\" in $recorddir; exiting..." >&2
    exit 1
fi

daq_setup_script=$( sed -r -n 's/^\s*DAQ\s+setup\s+script\s*:\s*(\S+).*$/\1/p' $recorddir/$runnum/boot.txt )

if [[ ! -e $daq_setup_script ]]; then
    cat >&2 <<EOF

Can't find DAQ setup script "$daq_setup_script"
listed in boot file for run $runnum ($recorddir/$runnum/boot.txt);
exiting...

EOF
    exit 1
fi

deviation_found=false

echo
echo -n "Checking that code is the same as was used in run $runnum..."
res=$( check_code_changes_since_run.sh $runnum )

if [[ -n $res ]]; then

    check_code_changes_since_run.sh $runnum

    cat<<EOF >&2

The code in the installation area which was used for run $runnum
either wasn't found or appears to have changed (details above). Unless
you're running this script with the --nostrict option, this attempt to
repeat run $runnum will not proceed.

EOF

    deviation_found=true
else
    echo "done."
fi

echo
echo -n "Checking that the known boardreaders list pointed to by DAQINTERFACE_KNOWN_BOARDREADERS_LIST is the same as was used in run $runnum..."

if [[ -n $( diff $DAQINTERFACE_KNOWN_BOARDREADERS_LIST $recorddir/$runnum/known_boardreaders_list.txt ) ]]; then
    cat <<EOF >&2

A difference was found in the contents of the file currently pointed
to by the DAQINTERFACE_KNOWN_BOARDREADERS_LIST environment variable
("$DAQINTERFACE_KNOWN_BOARDREADERS_LIST") and the file that was used
during run $runnum; unless you're running this script with the
--nostrict option, this attempt to repeat run $runnum will not
proceed. To address this warning, you can kill the current instance of
DAQInterface on your partition and execute the following two commands:

cp $recorddir/$runnum/known_boardreaders_list.txt /tmp/known_boardreaders_list.txt
export DAQINTERFACE_KNOWN_BOARDREADERS_LIST=/tmp/known_boardreaders_list.txt

and then relaunch DAQInterface.

EOF

    deviation_found=true
else
    echo "done."
fi

echo
echo -n "Checking that DAQInterface is being run on the same host as was used for run $runnum..."
daqinterface_host_from_run=$( sed -r -n 's/DAQInterface directory: ([^:]+).*/\1/p' $recorddir/$runnum/metadata.txt)
current_daqinterface_host=$( hostname )

if [[ $current_daqinterface_host != $daqinterface_host_from_run ]]; then

    cat<<EOF >&2

A difference was found between the host DAQInterface was run on for
run $runnum ($daqinterface_host_from_run) and the host you're
currently on ($current_daqinterface_host). Consequently, any artdaq
process specified to run on "localhost" in either the boot file or the
known boardreaders list won't run on $daqinterface_host_from_run,
unlike run $runnum. Unless you're running this script with the
--nostrict option, this attempt to repeat run $runnum will not
proceed.

EOF

    deviation_found=true
else
    echo "done."
    echo
fi

if ! $nostrict && $deviation_found ; then

cat<<EOF >&2

Exiting...

EOF

exit 1

fi


config=$( sed -r -n 's/^Config name: ([^#]+).*/\1/p' $recorddir/$runnum/metadata.txt )
comps=$( awk '/^Component/ { printf("%s ", $NF); }' $recorddir/$runnum/metadata.txt )

cmd="just_do_it.sh $recorddir/$runnum/boot.txt $seconds_to_run --config \"$config\" --comps \"$comps\""
echo "Executing $cmd"
eval $cmd

exit 0
