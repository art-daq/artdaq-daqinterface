import os
import stat
import re
import subprocess
from subprocess import Popen
import traceback
import shutil
import string
import socket

from rc.control.utilities import make_paragraph
from rc.control.utilities import get_commit_info
from rc.control.utilities import get_commit_info_filename
from rc.control.utilities import get_build_info
from rc.control.utilities import expand_environment_variable_in_string


def save_run_record_base(self):

    # Save the FHiCL documents which were used to initialize the
    # artdaq processes

    outdir = self.tmp_run_record

    try:
        os.makedirs(outdir)
    except Exception:
        raise Exception(
            make_paragraph("Exception raised during creation of %s" % (outdir))
        )
        return

    if not os.path.exists(outdir):
        raise Exception("Problem creating output directory %s" % (outdir))
        return

    for procinfo in self.procinfos:

        outf = open(outdir + "/" + procinfo.label + ".fcl", "w")

        outf.write(procinfo.fhicl_used)
        outf.close()

    # For good measure, let's also save the DAQInterface configuration file
    # JCF, Oct-25-2018: but save it with environment variables expanded (see Issue #21225)

    config_saved_name = "boot.txt"

    with open("%s/%s" % (outdir, config_saved_name), "w") as outf:
        with open(self.boot_filename) as inf:
            for line in inf.readlines():
                outf.write(expand_environment_variable_in_string(line))

    if not os.path.exists("%s/%s" % (outdir, config_saved_name)):
        self.alert_and_recover(
            "Problem creating file %s/%s" % (outdir, config_saved_name)
        )

    # As well as the DAQ setup script

    Popen(
        "cp -p " + self.daq_setup_script + " " + outdir + "/setup.txt",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).wait()

    if not os.path.exists(outdir + "/setup.txt"):
        self.alert_and_recover("Problem creating file %s/setup.txt" % (outdir))

    assert os.path.exists(os.environ["DAQINTERFACE_SETTINGS"])

    Popen(
        "cp -p " + os.environ["DAQINTERFACE_SETTINGS"] + " " + outdir + "/settings.txt",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).wait()

    if not os.path.exists(outdir + "/settings.txt"):
        self.alert_and_recover("Problem creating file " + outdir + "/settings.txt")

    assert os.path.exists(os.environ["DAQINTERFACE_KNOWN_BOARDREADERS_LIST"])

    Popen(
        "cp -p "
        + os.environ["DAQINTERFACE_KNOWN_BOARDREADERS_LIST"]
        + " "
        + outdir
        + "/known_boardreaders_list.txt",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).wait()

    if not os.path.exists(outdir + "/known_boardreaders_list.txt"):
        self.alert_and_recover(
            "Problem creating file " + outdir + "/known_boardreaders_list.txt"
        )

    ranksfilename = "%s/ranks.txt" % (outdir)

    with open(ranksfilename, "w") as ranksfile:
        ranksfile.write(
            "%-30s%-10s%-20s%-15s%-10s\n"
            % ("host", "port", "label", "subsystem", "rank")
        )
        ranksfile.write("\n")

        procinfos_sorted_by_rank = sorted(
            self.procinfos, key=lambda procinfo: procinfo.rank
        )
        for procinfo in procinfos_sorted_by_rank:
            host = procinfo.host
            if host == "localhost":
                host = socket.gethostname()
            ranksfile.write(
                "%-29s %-9s %-19s %-14s %-9d\n"
                % (
                    host,
                    procinfo.port,
                    procinfo.label,
                    procinfo.subsystem,
                    procinfo.rank,
                )
            )
    environfilename = "%s/environment.txt" % (outdir)

    with open(environfilename, "w") as environfile:
        for daqinterface_var in sorted(
            [varname for varname in os.environ if re.search(r"^DAQINTERFACE_", varname)]
        ):
            environfile.write(
                "export %s=%s\n"
                % (
                    daqinterface_var,
                    expand_environment_variable_in_string(os.environ[daqinterface_var]),
                )
            )

    # JCF, 11/20/14

    # Now save "metadata" about the run in the
    # "metadata_r<run #>.txt" file. This includes the
    # selected configuration, selected components, and commit
    # hashes of lbne-artdaq and lbnerc

    # JCF, Dec-4-2016: changed to metadata.txt, as this is executed
    # before the start transition

    outf = open(outdir + "/metadata.txt", "w")

    outf.write("Config name: %s\n" % (" ".join(self.subconfigs_for_run)))

    for i_comp, component in enumerate(sorted(self.daq_comp_list)):
        outf.write("Component #%d: %s\n" % (i_comp, component))

    outf.write("DAQInterface directory: %s:%s\n" % (socket.gethostname(), os.getcwd()))
    outf.write(
        "DAQInterface logfile: %s:%s\n"
        % (
            socket.gethostname(),
            expand_environment_variable_in_string(os.environ["DAQINTERFACE_LOGFILE"]),
        )
    )

    # Now save the commit hashes / versions of the packages listed in
    # $DAQINTERFACE_SETTINGS, along with the commit hash for
    # DAQInterface(if using DAQInterface from the repo) or version (if
    # using DAQInterface as a ups product)

    # JCF, Jul-9-2019
    # Add additional info along with that described above, as per Redmine Issue #22777

    outf.write(
        "\n# Two possible sets of fields provided below for code info, depending on if a git repo was available: "
    )
    outf.write(
        "\n# <git commit hash> <LoCs added on top of commit> <LoCs removed on top of commit> <git commit comment> <git commit time> <git branch> <BuildInfo build time (if available)> <BuildInfo version (if available)>"
    )
    outf.write(
        "\n# <package version> <BuildInfo build time (if available)> <BuildInfo version (if available)>\n\n"
    )

    buildinfo_packages = [
        pkg for pkg in self.package_hashes_to_save
    ]  # Directly assigning would make buildinfo_packages a reference, not a copy
    buildinfo_packages.append("artdaq-daqinterface")

    package_buildinfo_dict = get_build_info(buildinfo_packages, self.daq_setup_script)

    commit_info_fullpathname = "%s/%s" % (
        os.path.dirname(self.daq_setup_script),
        get_commit_info_filename("DAQInterface"),
    )
    daqint_full_path = "%s/srcs/artdaq-daqinterface" % (
        os.path.dirname(self.daq_setup_script)
    )
    if os.path.exists(commit_info_fullpathname):
        with open(commit_info_fullpathname) as commitfile:
            outf.write("%s" % (commitfile.read()))
    elif os.path.exists(daqint_full_path):
        outf.write("%s" % (get_commit_info("DAQInterface", daqint_full_path)))
    else:
        self.fill_package_versions(["artdaq-daqinterface"])
        outf.write(
            "DAQInterface commit/version: %s"
            % (self.package_versions["artdaq-daqinterface"])
        )

    outf.write(" %s\n\n" % (package_buildinfo_dict["artdaq-daqinterface"]))

    package_commit_dict = {}
    packages_whose_versions_we_need = []

    for pkgname in self.package_hashes_to_save:

        pkg_full_path = "%s/srcs/%s" % (os.path.dirname(self.daq_setup_script), pkgname)
        commit_info_fullpathname = "%s/%s" % (
            os.path.dirname(self.daq_setup_script),
            get_commit_info_filename(pkgname),
        )

        if os.path.exists(commit_info_fullpathname):
            with open(commit_info_fullpathname) as commitfile:
                package_commit_dict[pkgname] = commitfile.read()

        elif os.path.exists(pkg_full_path):
            try:
                package_commit_dict[pkgname] = get_commit_info(pkgname, pkg_full_path)
            except Exception:
                self.print_log("e", traceback.format_exc())
                self.alert_and_recover(
                    "An exception was thrown in get_commit_info; see traceback above for more info"
                )
                return
        else:
            # We'll throw this on the list of packages whose actual versions we need to figure out in real-time
            packages_whose_versions_we_need.append(pkgname)

    self.fill_package_versions(packages_whose_versions_we_need)

    for pkgname in packages_whose_versions_we_need:
        package_commit_dict[pkgname] = "%s commit/version: %s" % (
            pkgname,
            self.package_versions[pkgname],
        )

    for pkg in sorted(package_commit_dict.keys()):
        outf.write("%s" % (package_commit_dict[pkg]))
        outf.write(" %s\n\n" % (package_buildinfo_dict[pkg]))

    outf.write(
        "\nprocess management method: %s\n"
        % (os.environ["DAQINTERFACE_PROCESS_MANAGEMENT_METHOD"])
    )

    if self.manage_processes:

        logtuples = [
            ("process manager", self.process_manager_log_filenames),
            ("boardreader", self.boardreader_log_filenames),
            ("eventbuilder", self.eventbuilder_log_filenames),
            ("datalogger", self.datalogger_log_filenames),
            ("dispatcher", self.dispatcher_log_filenames),
            ("routingmanager", self.routingmanager_log_filenames),
        ]

        for logtuple in logtuples:

            outf.write("\n")
            outf.write("\n%s logfiles: " % logtuple[0])

            for filename in logtuple[1]:
                outf.write("\n" + filename)

    outf.write("\n")
    outf.close()

    for recorddir, dummy, recordfiles in os.walk(self.tmp_run_record):
        for recordfile in recordfiles:
            os.chmod("%s/%s" % (recorddir, recordfile), 0o444)

    try:
        shutil.copytree(self.tmp_run_record, self.semipermanent_run_record)
    except:
        self.print_log("w", traceback.format_exc())
        self.print_log(
            "w",
            make_paragraph(
                'Attempt to copy temporary run record "%s" into "%s" didn\'t work; keep in mind that %s will be clobbered next time you run on this partition'
                % (
                    self.tmp_run_record,
                    self.semipermanent_run_record,
                    self.tmp_run_record,
                )
            ),
        )

    self.print_log(
        "d",
        make_paragraph(
            "Saved run record in %s, will copy over to yet-to-be-created directory %s/<value of run number> on the start transition"
            % (outdir, self.record_directory)
        ),
        2,
    )


def save_metadata_value_base(self, key, value):

    metadata_filename = "%s/%s/metadata.txt" % (
        self.record_directory,
        str(self.run_number),
    )
    assert os.path.exists(metadata_filename)

    os.chmod(metadata_filename, 0o644)
    with open(metadata_filename, "a") as metadata_file:
        metadata_file.write("\n%s: %s\n" % (key, value))
    os.chmod(metadata_filename, 0o444)
