
cat <<EOF

Before reading on, keep in mind *this is NOT a substitute for reading
the DAQInterface manual* :
https://cdcvs.fnal.gov/redmine/projects/artdaq-utilities/wiki/Artdaq-daqinterface

The following list covers the most important environment variables
used to control DAQInterface's behavior. Remember you need to set a
variable *before* launching DAQInterface; it won't pick up the change
on-the-fly. If you wish to set a variable, do so in
$DAQINTERFACE_USER_SOURCEFILE, NOT in the standard DAQInterface source
file $ARTDAQ_DAQINTERFACE_DIR/source_me


///////////////////////////////////////////////////////////////////////

DAQINTERFACE_FHICL_DIRECTORY: the name of the directory containing the
configurations you can pass on the config transition. If set to "IGNORED",
this means the database is used.

DAQINTERFACE_KNOWN_BOARDREADERS_LIST: the name of the file containing
the list of possible boardreaders to select from for a run

DAQINTERFACE_LOGDIR: the directory in which the file which logs
DAQInterface's output to screen is located.

DAQINTERFACE_LOGFILE: the name of the file which logs DAQInterface's
output to screen. Defaults to
/tmp/daqinterface_${USER}/DAQInterface_partition\${DAQINTERFACE_PARTITION_NUMBER}.log.

Notice that since the variable name itself includes a reference to the
partition variable, you can't directly use it (e.g., "less \$DAQINTERFACE_LOGFILE"
wouldn't do what you'd think it would do)

DAQINTERFACE_PARTITION_NUMBER: The partition DAQInterface will run on. Defaults to 0.

DAQINTERFACE_PROCESS_MANAGEMENT_METHOD: The method DAQInterface uses
to control processes. Options are "direct", "pmt", and
"external_run_control".

DAQINTERFACE_PROCESS_REQUIREMENTS_LIST: The (optional) file users can
edit to control which processes are run-critical, assuming the process
management method is in "direct" mode

DAQINTERFACE_SETTINGS: The name of the file containing
unlikely-to-be-changed-often parameters controlling DAQInterface's
behavior (process timeouts, output directory for artdaq logfiles,
etc.)

DAQINTERFACE_USER_SOURCEFILE: The name of the experiment-defined script which
the generic DAQInterface source_me script will in turn source when you set up the
DAQInterface environment

//////////////////////////////////////////////////////////////////////

Keep in mind *this is NOT a substitute for reading the DAQInterface manual* :
https://cdcvs.fnal.gov/redmine/projects/artdaq-utilities/wiki/Artdaq-daqinterface

EOF
