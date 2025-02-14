#!/bin/env awk

/^Results:/ {

str=$0
error_state=0

print str
print ""

nsubs=gsub("Results:","",str)

if (nsubs != 1) {
    exit 1
}

print str
print ""

split(str, configs, ", ")
}

END {
    for (i in configs) {

	if (match(configs[i], "^[[:space:]]*$")) {
	    continue
	}

	# JCF, Mar-31-2017

	# The "RUN_CONFIG" token below, while seemingly unnecessary,
	# is used by the listconfigs_base function in
	# config_functions_database to distinguish the output of
	# artdaq-database's list_global_configs command from the
	# output artdaq-database creates when its setup script is
	# sourced. Therefore, please don't modify it without
	# accounting for the effect on listconfigs_base

	print "RUN_CONFIG: " configs[i]
    }
}
