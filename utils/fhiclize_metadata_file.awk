#!/bin/env awk

# JCF, Oct-27-2016

# At Gennadiy's request, this script will convert the DAQInterface
# configuration file and metadata file into legal FHiCL code

{

    # Comments in the metadata file don't need modification
    if ( $0 ~ /^\s*#/) {
	print $0
	next
    }

    if (components_section_active) {
	if ( $0 !~ /Component #[0-9]/) {
	    printf "components: ["
	    for (i = 1; i <= length(components); ++i) {
		if (i != length(components)) {
		    printf "\"%s\", ", components[i]
		} else {
		    printf "\"%s\"]\n", components[i]
		}
	    }
	    components_section_active = 0
	}
    }

    if (process_manager_section_active) {
	if ( $0 !~ /^\s*$/) {
	    process_managers[++process_manager_cntr] = $1
	    next
	} else {
	    printf "\nprocess_manager_logfiles: ["
	    for (i = 1; i <= length(process_managers); ++i) {
		if (i != length(process_managers)) {
		    printf "\"%s\", ", process_managers[i]
		} else {
		    printf "\"%s\"", process_managers[i]
		}
	    }
	    printf "]\n"
	    process_manager_section_active = 0
	}
    }


    if (boardreader_section_active) {
	if ( $0 !~ /^\s*$/) {
	    boardreaders[++boardreader_cntr] = $1
	    next
	} else {
	    printf "\nboardreader_logfiles: ["
	    for (i = 1; i <= length(boardreaders); ++i) {
		if (i != length(boardreaders)) {
		    printf "\"%s\", ", boardreaders[i]
		} else {
		    printf "\"%s\"", boardreaders[i]
		}
	    }
	    printf "]\n"
	    boardreader_section_active = 0
	}
    }


    if (eventbuilder_section_active) {
	if ( $0 !~ /^\s*$/) {
	    eventbuilders[++eventbuilder_cntr] = $1
	    next
	} else {
	    printf "\neventbuilder_logfiles: ["
	    for (i = 1; i <= length(eventbuilders); ++i) {
		if (i != length(eventbuilders)) {
		    printf "\"%s\", ", eventbuilders[i]
		} else {
		    printf "\"%s\"", eventbuilders[i]
		}
	    }
	    printf "]\n"
	    eventbuilder_section_active = 0
	}
    }

    if (routingmanager_section_active) {
	if ( $0 !~ /^\s*$/) {
	    routingmanagers[++routingmanager_cntr] = $1
	    next
	} else {
	    printf "\nroutingmanager_logfiles: ["
	    for (i = 1; i <= length(routingmanagers); ++i) {
		if (i != length(routingmanagers)) {
		    printf "\"%s\", ", routingmanagers[i]
		} else {
		    printf "\"%s\"", routingmanagers[i]
		}
	    }
	    printf "]\n"
	    routingmanager_section_active = 0
	}
    }

    if (datalogger_section_active) {
	if ( $0 !~ /^\s*$/) {
	    dataloggers[++datalogger_cntr] = $1
	    next
	} else {
	    printf "\ndatalogger_logfiles: ["
	    for (i = 1; i <= length(dataloggers); ++i) {
		if (i != length(dataloggers)) {
		    printf "\"%s\", ", dataloggers[i]
		} else {
		    printf "\"%s\"", dataloggers[i]
		}
	    }
	    printf "]\n"
	    datalogger_section_active = 0
	}
    }

    if (dispatcher_section_active) {
	if ( $0 !~ /^\s*$/) {
	    dispatchers[++dispatcher_cntr] = $1
	    next
	} else {
	    printf "\ndispatcher_logfiles: ["
	    for (i = 1; i <= length(dispatchers); ++i) {
		if (i != length(dispatchers)) {
		    printf "\"%s\", ", dispatchers[i]
		} else {
		    printf "\"%s\"", dispatchers[i]
		}
	    }
	    printf "]\n"
	    dispatcher_section_active = 0
	}
    }

    # Get the key / value pair; if there isn't one, then just continue

    colonloc=match($0, ":");

    if (RSTART != 0) {
	firstpart=substr($0, 1, RSTART);
	secondpart=substr($0, RSTART+1);
	sub("^[ +]", "", secondpart)

	if (firstpart ~ "Config name" || firstpart ~ "DAQInterface start time" ||
	    firstpart ~ "DAQInterface stop time" || firstpart ~ "Total events" ) {

	    firstpart = tolower(firstpart)
	    gsub(" ", "_", firstpart)

	} else if (firstpart ~ /Component #[0-9]/) {
	    components[++component_cntr] = secondpart
	    components_section_active = 1
	    next
	} else if (firstpart ~ /commit\/version/) {
	    gsub("[- ]", "_", firstpart)
	    sub("commit/version", "commit_or_version", firstpart)
	    gsub("\"", " ", secondpart); # Strip the quotes surrounding the commit
	    # comment, otherwise quotes added later
	    # will render illegal FHiCL
	} else if (firstpart ~ "pmt logfile") {
	    printf "pmt_logfiles_wildcard: \"%s\"\n", secondpart
	    next
	} else if (firstpart ~ "process management method") {
	    printf "process_management_method: \"%s\"\n", secondpart
	    next
	} else if (firstpart ~ "process manager logfiles") {
            process_manager_section_active = 1
	    next
	} else if (firstpart ~ "boardreader logfiles") {
	    boardreader_section_active = 1
	    next
	} else if (firstpart ~ "eventbuilder logfiles") {
	    eventbuilder_section_active = 1
	    next
	} else if (firstpart ~ "routingmanager logfiles") {
	    routingmanager_section_active = 1
	    next
	} else if (firstpart ~ "datalogger logfiles") {
	    datalogger_section_active = 1
	    next
	} else if (firstpart ~ "dispatcher logfiles") {
	    dispatcher_section_active = 1
	    next
	} else {
	    gsub("[- ]+", "_", firstpart)
	}

	if (secondpart !~ /^[0-9.]+$/ ) {
	    print firstpart " \"" secondpart "\"";
	} else {
	    print firstpart " " secondpart
	}

    } else {
	#print $0;
	next
    }
}

END {

    # This section exists because the last line may be a dispatcher
    # logfile line if we don't have time info in the metadata file

    if (dispatcher_section_active) {
	printf "\ndispatcher_logfiles: ["
	for (i = 1; i <= length(dispatchers); ++i) {
	    if (i != length(dispatchers)) {
		printf "\"%s\", ", dispatchers[i]
	    } else {
		printf "\"%s\"", dispatchers[i]
	    }
	}
	printf "]\n"
    }

}
