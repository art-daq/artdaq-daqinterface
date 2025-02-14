#!/bin/bash

# JCF, Oct. 14, 2015

# A simple script which, based on the info in the run records
# directory, will tell you the run start time, configuration, and
# components of the last N runs

# Feedback on how to make this script more useful will be welcome...

if [ $# != 1 ] ; then
     echo "Usage: $0 <last N runs>"
     exit 1
fi

nruns=$1

. $ARTDAQ_DAQINTERFACE_DIR/bin/exit_if_bad_environment.sh
. $ARTDAQ_DAQINTERFACE_DIR/bin/diagnostic_tools.sh

echo

for dir in $( ls -tr1 $recorddir | tail -$nruns  ); do

    metadata_file=$recorddir/$dir/metadata.txt

    if [[  -e $metadata_file ]]; then

	datestring=$( ls -l $metadata_file | awk '{print $6,$7,$8}' )

	echo -n Run ${dir} "("${datestring}") : "
	awk '/Config/ { sub("Config name: *", ""); config=$0 } \
             /Component/ { components = components $NF " " } \
             END { printf("%-30s: %s\n", config, components); } ' \
	    $metadata_file

    else
	echo "Warning: unable to find expected file $metadata_file "
    fi
done

echo
