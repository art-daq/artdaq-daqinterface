#!/bin/env bash

badargs=false
cmd=$1
xmlrpc_arg=
translated_cmd=

. $ARTDAQ_DAQINTERFACE_DIR/bin/exit_if_bad_environment.sh
. $ARTDAQ_DAQINTERFACE_DIR/bin/daqinterface_functions.sh
daqinterface_preamble

. $ARTDAQ_DAQINTERFACE_DIR/bin/diagnostic_tools.sh  # provides recorddir

. $ARTDAQ_DAQINTERFACE_DIR/bin/package_setup.sh xmlrpc_c

xmlrpc_retval=$?

if [[ "$xmlrpc_retval" != "0" ]]; then
    echo "Problem attempting to setup xmlrpc_c package" >&2
    exit 40
fi

case $cmd in
    "boot")
	test $# -gt 1 || badargs=true
	translated_cmd="booting"
	boot_filename=$2
	xmlrpc_arg="boot_filename:s/"${boot_filename}
	;;
    "config")
	test $# -gt 1 || badargs=true
	translated_cmd="configuring"

	xmlrpc_arg="config:array/("
	shift
	for subconfig in $@ ; do
	    if [[ "$subconfig" != "${@: -1}" ]] ; then   # "${@: -1}" is the last argument
		xmlrpc_arg="${xmlrpc_arg}s/${subconfig},"
	    else
		xmlrpc_arg="${xmlrpc_arg}s/${subconfig})"
	    fi
	done
	;;
    "start")
	test $# == 1 || test $# == 2 || badargs=true
	translated_cmd="starting"

	runnum=0
        highest_runnum=$( ls -1 $recorddir | sort -n | tail -1 )

	if [[ $# == 1 ]]; then
            runnum=$((highest_runnum + 1))
        else
            runnum=$2
        fi

	xmlrpc_arg="run_number:i/"$runnum
	;;
    "enable")
	test $# == 1 || badargs=true
        translated_cmd="enabling"
	;;
    "disable")
	test $# == 1 || badargs=true
        translated_cmd="disabling"
	;;
    "stop")
	test $# == 1 || badargs=true
	translated_cmd="stopping"
	;;
    "shutdown")
	test $# == 1 || badargs=true
	translated_cmd="shutting"
	;;
    "terminate")
	test $# == 1 || badargs=true
	translated_cmd="terminating"
	;;
    *)
	echo "Unknown command \"$cmd\" passed" >&2
	exit 30
	;;
esac

if [[ "$badargs" = true ]]; then
    echo "Incorrect arguments passed to $0" >&2
    exit 20
fi


full_cmd="xmlrpc http://localhost:$DAQINTERFACE_PORT/RPC2 state_change daqint "${translated_cmd}

if [[ -n $xmlrpc_arg ]]; then
    full_cmd=${full_cmd}" 'struct/{"${xmlrpc_arg}"}'"
else
    full_cmd=${full_cmd}" 'struct/{ignored_variable:i/999}' "
fi

echo $full_cmd
eval $full_cmd
exit 0
