#!/bin/bash

if [ $# != 4 ] ; then
     echo "Usage: $0 <last N runs> <component name> <component label> <string to search>"
     echo
     echo "Note that if you don't care about the component label, you can replace it with an asterisk in quotes or with a dash, i.e., a \"*\" or -"
     echo
     exit 1
fi

nruns=$1
compname=$2
label=$3
searchstring=$4

. $ARTDAQ_DAQINTERFACE_DIR/bin/exit_if_bad_environment.sh
. $ARTDAQ_DAQINTERFACE_DIR/bin/diagnostic_tools.sh

echo

for run in $( ls -tr1 $recorddir | tail -$nruns  ); do


    metadata_filename=$recorddir/$run/metadata.txt

    if [[  -e $metadata_filename ]]; then

	datestring=$( ls -l $metadata_filename | awk '{print $6,$7,$8}' )

	hascomp=$( awk '{ if ( $0 ~ /Component/ ) { components = components $NF " " } } \
             END { if ( components ~ /'$compname'/ ) { print "TRUE"} } ' \
	    $metadata_filename )

	# If we found the desired component in the given run, let's
	# see if the desired string is in the logfile

	if [[ "$hascomp" == "TRUE" ]]; then

	    config=$( sed -r -n '/Config/s/^.*\s+(\S+)\s*$/\1/p' $metadata_filename  )

	    fileglob=$( sed -r -n '/pmt logfile/s/.*:(.*)/\1/p' $metadata_filename )

	    foundstring=0

	    if [[ -n $fileglob ]]; then

		files_time_ordered=$( ls -tr $fileglob | tr "\n" " ")

		res=$( sed -r -n '/Started run '$run'/,/Started run '$((run+1))'/{/'"$label"'/{N;/'"$searchstring"'/p}}' $files_time_ordered )
		if [[ -n $res ]]; then
		    foundstring=1
		else
		    foundstring=0
		fi

	    else
		echo "Unable to find pmt logfiles in $metadata_filename" >&2
		continue
	    fi

	    echo -n "$run (${datestring}): "

	    if [[ "$foundstring" == "1" ]]; then
		echo " X"
	    else
		echo
	    fi
	fi

    else
	echo "Warning: unable to find expected file $metadata_filename "
    fi
done

echo
