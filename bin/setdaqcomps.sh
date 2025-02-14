#!/bin/env bash

if [[ "$#" == "0" ]]; then

    cat>&2<<EOF

        No arguments were supplied to this script: you need to provide
        a list of boardreaders. For allowed boardreader names, execute
        "listdaqcomps.sh"

EOF
    exit 1
fi


components=$@

. $ARTDAQ_DAQINTERFACE_DIR/bin/exit_if_bad_environment.sh
. $ARTDAQ_DAQINTERFACE_DIR/bin/daqinterface_functions.sh
daqinterface_preamble

scriptdir="$(dirname "$0")"
. $scriptdir/package_setup.sh xmlrpc_c

xmlrpc_retval=$?

if [[ "$xmlrpc_retval" != "0" ]]; then
    echo "Problem attempting to setup xmlrpc_c package" >&2
    exit 40
fi

components_file=$DAQINTERFACE_KNOWN_BOARDREADERS_LIST

if [[ ! -e $components_file ]]; then

    cat>&2<<EOF

    Unable to find file containing allowed components, "$components_file"

EOF

    exit 10
fi


num_components=$( echo $components | wc -w)
comp_cntr=0

for comp in $components; do

    comp_cntr=$((comp_cntr + 1))

    comp_line=$( grep -E "^$comp " $components_file )

    if [[ -n $comp_line ]]; then
	host=$( echo $comp_line | awk '{print $2}' )
	port=$( echo $comp_line | awk '{print $3}' )
	subsystem=$( echo $comp_line | awk '{print $4}' )
	allowed_processors=$( echo $comp_line | awk '{print $5}' )

	# sed command below says "Grab a quoted sixth field, if it exists"
	prepend=$( echo $comp_line | sed -r -n "s/^\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(\"[^\"]+\")/\1/p" )


	if [[ -z $prepend ]] && (( $( echo $comp_line | awk '{ print NF  }' ) >= 6 )); then

	    cat<<EOF >&2

An unquoted sixth field was found in $DAQINTERFACE_KNOWN_BOARDREADERS_LIST on this line:

$comp_line

This suggests that a command-to-be-prepended to artdaq process launch
was unquoted, which is a syntax error. Exiting...

EOF

exit 1

	fi


	#defaults
	port=${port:-"-1"}
	subsystem=${subsystem:-"1"}

	xmlrpc_arg=${xmlrpc_arg}${comp}":array/(s/"${host}","${port}","${subsystem}

	if [[ -n $allowed_processors ]]; then
	    xmlrpc_arg=${xmlrpc_arg}","${allowed_processors}
	fi

	if [[ -n $prepend ]]; then
	    xmlrpc_arg=${xmlrpc_arg}","${prepend}
	fi

	xmlrpc_arg=${xmlrpc_arg}")"

	test $comp_cntr != $num_components && xmlrpc_arg=${xmlrpc_arg}","
    else

	cat>&2<<EOF

	Unable to find listing for component "$comp" in
	$components_file; will not send component list to DAQInterface

EOF

	exit 20
    fi
done

xmlrpc http://localhost:$DAQINTERFACE_PORT/RPC2 setdaqcomps "struct/{$xmlrpc_arg}"

exit $?
