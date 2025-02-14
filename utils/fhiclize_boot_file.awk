#!/bin/env awk

BEGIN {

    # Subsystem variables
    id = "not set"
    source = "not set"
    destination = "not set"

    subsystem_tokens["id"] = "now defined"
    subsystem_tokens["source"] = "now defined"
    subsystem_tokens["destination"] = "now defined"

    # Process variables
    name = "not set"
    label = "not set"
    host = "not set"
    port = "not set"
    subsystem = "not set"

    process_names["BoardReader"] = "now defined"
    process_names["EventBuilder"] = "now defined"
    process_names["DataLogger"] = "now defined"
    process_names["Dispatcher"] = "now defined"
    process_names["RoutingManager"] = "now defined"

    process_tokens["host"] = "now defined"
    process_tokens["port"] = "now defined"
    process_tokens["label"] = "now defined"
    process_tokens["subsystem"] = "now defined"
}

function chk_sys_subsys()
{
	if (label != "not set") {   # Shorthand for "we've got info for a process"
	    procinfos[label] = sprintf("name: \"%s\"\nlabel: \"%s\"\nhost: \"%s\"", name, label, host)
	    if (port != "not set") {
		procinfos[label] = sprintf("%s\nport: %d", procinfos[label], port)
	    }

	    if (subsystem != "not set") {
		procinfos[label] = sprintf("%s\nsubsystem: \"%s\"", procinfos[label], subsystem)
	    }

	    procinfos[label] = sprintf("%s\n", procinfos[label])

	    name = "not set"
	    label = "not set"
	    host = "not set"
	    port = "not set"
	    subsystem = "not set"

	} else if (id != "not set" ) { # Shorthand for "we've got info for a subsystem"

	    subsystems[id] = sprintf("id: \"%s\"", id)
	    if (source != "not set") {
		subsystems[id] = sprintf("%s\nsource: \"%s\"", subsystems[id], source)
	    }
	    if (destination != "not set") {
		subsystems[id] = sprintf("%s\ndestination: \"%s\"", subsystems[id], destination)
	    }

	    subsystems[id] = sprintf("%s", subsystems[id])

	    id = "not set"
	    source = "not set"
	    destination = "not set"
	}
}

{
    match($0, "^\\s*#")  # Skip commented lines
    if (RSTART != 0) {
       next
    }

   # And blank lines, also interpreting them as the delimiter for a given
   # process's collection of info

    match($0, "^\\s*$")
    if (RSTART != 0) {
		chk_sys_subsys()
	next
    }

    # Get the key / value pair; if there isn't one, then just continue

    match($0, ":");

    if (RSTART == 0) {
	next
    } else {
	firstpart=substr($0, 1, RSTART-1);
	secondpart=substr($0, RSTART+1);

	sub("^\\s*","", firstpart);
	sub("\\s*$","", firstpart);
	gsub("\\s+", "_", firstpart);

	sub("^\\s*","", secondpart);
	sub("\\s*$","", secondpart);

	for (subsystem_token in subsystem_tokens) {
	    keymatch = sprintf("Subsystem_%s", subsystem_token)

	    if (firstpart ~ keymatch) {
		if (subsystem_token == "id") {
		    id = secondpart
		} else if (subsystem_token == "source") {
		    source = secondpart
		} else if (subsystem_token == "destination") {
		    destination = secondpart
		}
		next
	    }
	}

	for (process_name in process_names) {
	    for (process_token in process_tokens) {
		keymatch = sprintf("%s_%s", process_name, process_token)

		if (firstpart ~ keymatch) {
		    name = process_name

		    if (process_token == "label") {
			label = secondpart
		    } else if (process_token == "host" ) {
			host = secondpart
		    } else if ( process_token == "port" ) {
			port = secondpart
		    } else if ( process_token == "subsystem" ) {
			subsystem = secondpart
		    }

		    next
		}
	    }
	}

	if ((secondpart !~ /^[0-9.]+$/ || gsub("\\.", ".", secondpart) > 1) && (secondpart !~ /^\".*\"$/) && (secondpart !~ /^\[.*\]$/)) {
	    print firstpart ": \"" secondpart "\"";
	} else {
	    print firstpart ": " secondpart
	}
    }
}

END {

	chk_sys_subsys()

    if (length(subsystems) > 0) {
	printf("\nsubsystem_settings: [\n{\n")
	cntr = 1
	for (id in subsystems) {
	    printf("%s", subsystems[id])
	    if (cntr < length(subsystems)) {
		printf("\n},\n{\n")
	    }
	    cntr++
	}
	printf("\n}\n]\n")
    }

    printf("\nartdaq_process_settings: [\n{\n")
    cntr = 1
    for (label in procinfos) {
	printf("%s", procinfos[label])
	if (cntr < length(procinfos)) {
	    printf("},\n{\n")
	}
	cntr++
    }
    printf("}\n]\n")
}
