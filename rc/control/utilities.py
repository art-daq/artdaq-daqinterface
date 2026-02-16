#!/usr/bin/env python

import os
import re
import string
import socket
import shutil
import sys
import stat

import subprocess
from subprocess import Popen

from time import sleep
from time import time

from threading import Thread


# Raise exceptions from threads https://stackoverflow.com/questions/2829329/catch-a-threads-exception-in-the-caller-thread
class RaisingThread(Thread):
    def run(self):
        self._exc = None
        try:
            super().run()
        except Exception as e:
            self._exc = e

    def join(self, timeout=None):
        super().join(timeout=timeout)
        if self._exc:
            raise self._exc


def expand_environment_variable_in_string(line):

    res = re.search(r"^(.*)(\$[{A-Za-z][A-Za-z}_0-9]*)(.*)", line)

    if res:
        environ_var = res.group(2)
        environ_var = environ_var.strip("${}")

        if environ_var in os.environ.keys():
            if line[-1] == "\n":
                line = res.group(1) + os.environ[environ_var] + res.group(3) + "\n"
            else:
                line = res.group(1) + os.environ[environ_var] + res.group(3)
        else:
            raise Exception(
                'Expanding line "%s", unable to find definition for environment variable "%s"'
                % (line.strip(), environ_var)
            )

    return line


def make_paragraph(userstring, chars_per_line=75):
    userstring.strip()

    string_index = chars_per_line
    previous_string_index = -1
    ignore_algorithm = False

    userstring = userstring.replace("\n", " ")

    while len(userstring) - string_index > 0:

        if not ignore_algorithm:
            while not userstring[string_index].isspace():
                string_index -= 1
                assert string_index >= 0
        else:
            while not userstring[string_index].isspace():
                string_index += 1
                if len(userstring) <= string_index:
                    return "\n" + userstring

        userstring = userstring[:string_index] + "\n" + userstring[string_index + 1 :]

        string_index += chars_per_line

        # If there's a token with no whitespace which is longer
        # than chars_per_line characters (as may be the case with
        # some full pathnames, e.g.) there's a risk of an infinite
        # loop without the external logic below

        if previous_string_index == string_index:
            ignore_algorithm = True

        previous_string_index = string_index

    return "\n" + userstring


# JCF, 3/11/15

# "get_pids" is a simple utility function which will go to the
# requested host (defaults to the local host), and searches for a
# process by grep-ing for the passed greptoken in the process
# table returned by "ps aux". It returns a (possibly empty) list
# of the process IDs found

# JCF, Dec-12-2018

# Have "grepresults" serve as a pass-by-reference in which, if the caller
# thinks not just the pid list but the actual lines grep'd for may be
# of interest - e.g., for diagnostics or debugging - they can save
# this result


def host_is_local(host):
    return (
        host == "localhost"
        or ("HOSTNAME" in os.environ and host == os.environ["HOSTNAME"])
        or get_short_hostname() in host
    )


def get_pids(greptoken, host="localhost", grepresults=None):

    cmd = 'ps aux | grep "%s" | grep -v grep' % (greptoken)

    if not host_is_local(host):
        cmd = "ssh -o BatchMode=yes -x %s '%s'" % (host, cmd)

    proc = Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )

    out, err = proc.communicate()
    lines = []
    if len(out) > 0:
        lines = out.strip().split("\n")
    if len(err) > 0:
        raise Exception(
            "SSH process for retrieving PIDs had the following error output:\n %s"
            % (err)
        )

    if grepresults is not None:
        for line in lines:
            grepresults.append(
                line
            )  # Clunkier than a straight assignment, but needed for pass-by-reference

    pids = [line.split()[1] for line in lines]

    return pids


# [Comment added by KAB, 17-Apr-2018]
# This function returns the contents of the FHiCL table that immediately
# follows the specified string (tablename).  It does not require that
# 'tablename' actually be a FHiCL key.
def table_range(fhiclstring, tablename, startingloc=0):

    # 13-Apr-2018, KAB: added the startingloc argument so that this function can
    # be used to find more than the first instance of the tablename in the string.
    loc = fhiclstring.find(tablename, startingloc)

    if loc == -1:
        return (-1, -1)

    # JCF, Apr-18-2019
    # Account for the scenario where in the FHiCL we have something like
    # table_whose_range_we_want: @local::table_which_gets_assigned_to_table_whose_range_we_want

    res = re.search(r"%s\s*:\s*@local::(\S+)" % tablename, fhiclstring[loc:])
    if res:
        original_table_name = res.group(1)
        return table_range(fhiclstring, original_table_name)

    # JCF, Aug-1-2019

    # Check that what we have is actually a table - this is prompted
    # by an email Kurt sent on June 26, 12:46 PM. If it's not, then
    # keep searching further on in the FHiCL blob.

    res = re.search(r"^%s\s*:\s*{" % tablename, fhiclstring[loc:])
    if not res:
        (offset_start, offset_end) = table_range(fhiclstring[loc + 1 :], tablename)
        if (offset_start, offset_end) != (-1, -1):
            return (loc + 1 + offset_start, loc + 1 + offset_end)
        else:
            return (-1, -1)

    open_brace_loc = fhiclstring[loc:].index("{")

    close_braces_needed = 1
    close_brace_loc = -1

    for i_char, char in enumerate(fhiclstring[(loc + open_brace_loc + 1) :]):

        if char == "{":
            close_braces_needed += 1
        elif char == "}":
            close_braces_needed -= 1

        if close_braces_needed == 0:
            close_brace_loc = i_char
            break

    if close_brace_loc == -1:
        raise Exception(
            'Unable to find close brace for requested table "%s"' % tablename
        )

    return (loc, loc + open_brace_loc + 1 + close_brace_loc + 1)


# 17-Apr-2018, KAB: added this function to find the *enclosing* FHiCL
# table for the specified string. This can be useful when looking for
# a table that has a desirable FHiCL value, and we want to fetch the
# contents of the entire table.
def enclosing_table_range(fhiclstring, searchstring, startingloc=0):

    loc = fhiclstring.find(searchstring, startingloc)

    if loc == -1:
        return (-1, -1)

    braces_before = [
        (i + startingloc, c)
        for (i, c) in enumerate(fhiclstring[startingloc:loc])
        if (c == "}" or c == "{")
    ]

    opening_count = 0
    closing_count = 0
    opening_position = -1

    for brace in reversed(braces_before):
        if brace[1] == "{":
            opening_count += 1
        else:
            closing_count += 1

        if opening_count - closing_count == 1:
            opening_position = brace[0]
            break

    if opening_position == -1:
        return (-1, -1)

    braces_after = [
        (i + loc, c)
        for (i, c) in enumerate(fhiclstring[loc:])
        if (c == "}" or c == "{")
    ]

    opening_count = 0
    closing_count = 0
    closing_position = -1

    for brace in braces_after:
        if brace[1] == "}":
            closing_count += 1
        else:
            opening_count -= 1

        if closing_count - opening_count == 1:
            closing_position = brace[0]
            break

    if closing_position == -1:
        return (-1, -1)

    return (opening_position, closing_position + 1)


# 26-Nov-2018, ELF: This function finds the name of the enclosing table
# for the specified string. This is used when determining which
# destinations block is currently being filled during bookkeeping.
def enclosing_table_name(fhiclstring, searchstring, startingloc=0):

    (open_brace_loc, close_brace_loc_will_be_ignored) = enclosing_table_range(
        fhiclstring, searchstring, startingloc
    )

    colon_loc = fhiclstring.rindex(":", 0, open_brace_loc)

    while fhiclstring[colon_loc - 1] == " ":
        colon_loc -= 1

    name = re.sub(".*\s", "", fhiclstring[:colon_loc])

    return name


def commit_check_throws_if_failure(packagedir, commit_hash, date, request_after):

    assert os.path.exists(packagedir), (
        "Directory %s doesn't appear to exist; a check should occur earlier in the program for this"
        % (packagedir)
    )

    cmds = []
    cmds.append("cd " + packagedir)
    cmds.append("git log | grep %s" % (commit_hash))

    proc = Popen(
        ";".join(cmds),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="UTF-8",
    )
    proclines = proc.stdout.readlines()

    if request_after and len(proclines) != 1:
        raise Exception(
            make_paragraph(
                'Unable to find expected git commit hash %s (%s) in directory "%s"; this means the version of code in that directory isn\'t the one expected'
                % (commit_hash, date, packagedir)
            )
        )
    elif not request_after and len(proclines) != 0:
        raise Exception(
            make_paragraph(
                'Unexpectedly found git commit hash %s (%s) in directory "%s"; this means the version of code in that directory isn\'t the one expected'
                % (commit_hash, date, packagedir)
            )
        )


def is_msgviewer_running():

    for line in Popen(
        "ps u",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="UTF-8",
    ).stdout.readlines():
        if (
            "msgviewer" in line
            and "DAQINTERFACE_TTY" in os.environ
            and os.environ["DAQINTERFACE_TTY"] in line
        ):
            return True

    return False


def execute_command_in_xterm(home, cmd):

    if not os.path.exists(os.environ["HOME"] + "/.Xauthority"):
        raise Exception("Unable to find .Xauthority file in home directory")

    if home != os.environ["HOME"]:
        status = Popen(
            "cp -p ~/.Xauthority %s" % (home),
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).wait()
        if status != 0:
            raise Exception(
                "Unable to copy .Xauthority file into directory %s; do you have write permissions there?"
                % (home)
            )

    # JCF, May-11-2017

    # The following chant to xterm is influenced both by Ron's
    # implementation of xt_cmd.sh in artdaq-demo as well as the info
    # found at
    # https://superuser.com/questions/363614/leave-xterm-open-after-task-is-complete

    fullcmd = (
        'env -i SHELL=/bin/bash PATH=/usr/bin:/bin LOGNAME=%s USER=%s  DISPLAY=%s  REALHOME=%s HOME=%s KRB5CCNAME=%s  xterm -geometry 100x33+720+0 -sl 2500 -e "%s ; read " &'
        % (
            os.environ["LOGNAME"],
            os.environ["USER"],
            os.environ["DISPLAY"],
            os.environ["HOME"],
            home,
            os.environ["KRB5CCNAME"],
            cmd,
        )
    )

    Popen(
        fullcmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ).wait()


def date_and_time():
    return (
        Popen(
            'date +"%a %b %e %H:%M:%S %Z %Y"',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="UTF-8",
        )
        .stdout.readlines()[0]
        .strip()
    )


def date_and_time_more_precision():
    return (
        Popen(
            "date +%a_%b_%d_%H:%M:%S.%N | sed -r 's/_/ /g'",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="UTF-8",
        )
        .stdout.readlines()[0]
        .strip()
    )


def date_and_time_filename():
    return (
        Popen(
            "date +%Y%m%d%H%M%S",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="UTF-8",
        )
        .stdout.readlines()[0]
        .strip()
    )


def construct_checked_command(cmds):

    checked_cmds = []

    for cmd in cmds:

        checked_cmds.append(cmd)

        if not re.search(r"\s*&\s*$", cmd):
            check_cmd = (
                'if [[ "$?" != "0" ]]; then echo %s: Nonzero return value from the following command: "%s" >> /tmp/daqinterface_checked_command_failures_%s.log; exit 1; fi '
                % (date_and_time(), cmd, os.environ["USER"])
            )
            checked_cmds.append(check_cmd)

    total_cmd = " ; ".join(checked_cmds)

    return total_cmd


def reformat_fhicl_documents(setup_fhiclcpp, procinfos):

    if not os.path.exists(setup_fhiclcpp):
        raise Exception(
            make_paragraph(
                "Expected fhiclcpp setup script %s doesn't appear to exist"
                % (setup_fhiclcpp)
            )
        )

    cmd = "grep -c ^processor /proc/cpuinfo"

    nprocessors = (
        Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="UTF-8",
        )
        .stdout.readlines()[0]
        .strip()
    )

    if not re.search(r"^[0-9]+$", nprocessors):
        raise Exception(
            make_paragraph(
                'A problem occurred when DAQInterface tried to execute "%s"; result was not an integer'
                % (cmd)
            )
        )

    reformat_indir = (
        Popen(
            "mktemp -d",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="UTF-8",
        )
        .stdout.readlines()[0]
        .strip()
    )
    reformat_outdir = (
        Popen(
            "mktemp -d",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="UTF-8",
        )
        .stdout.readlines()[0]
        .strip()
    )

    for procinfo in procinfos:
        with open(
            "%s/%s.fcl" % (reformat_indir, procinfo.label), "w"
        ) as preformat_fhicl_file:
            preformat_fhicl_file.write(procinfo.fhicl_used)

    cmds = []
    cmds.append(
        "if [[ -z $( command -v fhicl-dump ) ]]; then source %s; fi" % (setup_fhiclcpp)
    )

    cmds.append("cd %s" % (reformat_indir))

    xargs_cmd = (
        "find ./ -name \*.fcl -print | xargs -I {} -n 1 -P %s fhicl-dump -l none -c {} -o %s/{}"
        % (nprocessors, reformat_outdir)
    )

    cmds.append("echo About to execute '%s'" % (xargs_cmd))
    cmds.append(xargs_cmd)

    out = Popen(
        "\n".join(cmds),
        shell=True,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        encoding="UTF-8",
    )

    out_comm = out.communicate()

    out_stdout = out_comm[0]
    out_stderr = out_comm[1]
    status = out.returncode

    if status != 0:

        if out_stdout is not None:
            print(out_stdout)

        if out_stderr is not None:
            print(out_stderr)

        raise Exception(
            "There was a problem reformatting the FHiCL documents found in %s; this is very likely due to illegal FHiCL syntax somewhere. See above for more info."
            % (reformat_indir)
        )

    reformatted_fhicl_strings = []
    for label in [procinfo.label for procinfo in procinfos]:
        with open("%s/%s.fcl" % (reformat_outdir, label)) as reformatted_fhicl_file:
            reformatted_fhicl_strings.append(reformatted_fhicl_file.read())

    shutil.rmtree(reformat_indir)
    shutil.rmtree(reformat_outdir)

    return reformatted_fhicl_strings


# JCF, 12/2/14

# Given the directory name of a git repository, this will return
# the most recent hash commit in the repo


def get_commit_hash(gitrepo):

    if not os.path.exists(gitrepo):
        return "Unknown"

    cmds = []
    cmds.append("cd %s" % (gitrepo))
    cmds.append("git log | head -1 | awk '{print $2}'")

    proc = Popen(
        ";".join(cmds),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="UTF-8",
    )
    proclines = proc.stdout.readlines()

    if len(proclines) != 1 or len(proclines[0].strip()) != 40:
        raise Exception(
            make_paragraph(
                'Commit hash for "%s" not found; this was requested in the "packages_hashes_to_save" list found in %s'
                % (gitrepo, os.environ["DAQINTERFACE_SETTINGS"])
            )
        )

    commit_hash = proclines[0].strip()

    cmds = []
    cmds.append("cd %s" % (gitrepo))
    cmds.append('git diff --unified=0 | grep "^-[^-][^-]" | wc -l')
    num_subtracted_lines = (
        Popen(
            ";".join(cmds),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="UTF-8",
        )
        .stdout.readlines()[0]
        .strip()
    )

    cmds = []
    cmds.append("cd %s" % (gitrepo))
    cmds.append('git diff --unified=0 | grep "^+[^+][^+]" | wc -l')
    num_added_lines = (
        Popen(
            ";".join(cmds),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="UTF-8",
        )
        .stdout.readlines()[0]
        .strip()
    )

    return "%s %s %s" % (commit_hash, num_subtracted_lines, num_added_lines)


def get_commit_comment(gitrepo):

    max_length = 50

    if not os.path.exists(gitrepo):
        return ""

    cmds = []
    cmds.append("cd %s" % (gitrepo))
    cmds.append("git log --format=%B -n 1 HEAD")
    proc = Popen(
        ";".join(cmds),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="UTF-8",
    )

    proclines = proc.stdout.readlines()
    single_line_comment = proclines[0]
    for line in proclines[1:]:
        single_line_comment += " " + line

    for badchar in ["\n", '"', "'"]:
        single_line_comment = single_line_comment.replace(badchar, "")

    if len(single_line_comment) > max_length:
        single_line_comment = single_line_comment[0:max_length] + "..."

    return single_line_comment


def get_commit_time(gitrepo):

    if not os.path.exists(gitrepo):
        return "Unknown"

    cmds = []
    cmds.append("cd %s" % (gitrepo))
    cmds.append("git log -1 | sed -r -n 's/Date:\\s+(.*)/\\1/p'")

    proc = Popen(
        ";".join(cmds),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="UTF-8",
    )
    proclines = proc.stdout.readlines()

    return proclines[0].strip()


def get_commit_branch(gitrepo):
    if not os.path.exists(gitrepo):
        return "Unknown"

    cmds = []
    cmds.append("cd %s" % (gitrepo))
    cmds.append("git branch | sed -r -n 's/^\\* (\\S+)/\\1/p'")

    proc = Popen(
        ";".join(cmds),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="UTF-8",
    )
    proclines = proc.stdout.readlines()

    return proclines[0].strip()


# JCF, Jul-6-2019

# Note to self: if you modify the label before the colon below, make sure you make commensurate
# modifications in save_run_record...


def get_commit_info(pkgname, gitrepo):
    return '%s commit/version: %s "%s" "%s" "%s"' % (
        pkgname,
        get_commit_hash(gitrepo),
        get_commit_comment(gitrepo),
        get_commit_time(gitrepo),
        get_commit_branch(gitrepo),
    )


def get_commit_info_filename(pkgname):
    return "%s_commit_info.txt" % (pkgname)


def get_build_info(pkgnames, setup_script):
    def parse_buildinfo_file(buildinfo_filename):
        # print(f"Searching for verison/timestamp info in {buildinfo_filename}")
        buildinfo_version = '"version from BuildInfo undetermined"'
        buildinfo_time = '"time from BuildInfo undetermined"'

        found_buildinfo_version = False
        found_buildinfo_time = False

        with open(buildinfo_filename) as inf:
            for line in inf.readlines():

                res = re.search(r"setPackageVersion\s*\(\s*(\".*\")\s*\)", line)
                if res:
                    buildinfo_version = res.group(1)
                    found_buildinfo_version = True
                    continue

                res = re.search(r"setBuildTimestamp\s*\(\s*(\".*\")\s*\)", line)
                if res:
                    buildinfo_time = res.group(1)
                    found_buildinfo_time = True
                    continue

        if not found_buildinfo_version or not found_buildinfo_time:
            print(
                "Failed to find one (or both of) buildinfo time and version in %s!"
                % (buildinfo_filename)
            )

        return "%s %s" % (buildinfo_time, buildinfo_version)

    pkg_build_infos = {}
    cmds = []
    cmds.append(". %s" % (setup_script))

    for pkgname in pkgnames:
        cmds.append(f"spack cd -i {pkgname};pwd")

    proc = Popen(
        ";".join(cmds),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="UTF-8",
    )
    stdoutlines = proc.stdout.readlines()

    for pkgname in pkgnames:

        buildinfo_time = '"time from BuildInfo undetermined"'
        buildinfo_version = '"version from BuildInfo undetermined"'
        pkg_build_infos[pkgname] = f"{buildinfo_time} {buildinfo_version}"

        found_spack_package = False
        package_line_number = -1
        for i_l, line in enumerate(stdoutlines):
            if re.search(rf"/{pkgname}-v?[0-9]", line):
                found_spack_package = True
                package_line_number = i_l
                break

        if found_spack_package:
            package_dir = stdoutlines[package_line_number].strip()

            buildinfo_file = (
                f"{package_dir}/source/{pkgname}/BuildInfo/GetPackageBuildInfo.cc"
            )

            pkg_build_infos[pkgname] = parse_buildinfo_file(buildinfo_file)
            continue
        else:
            mpd_basedir = os.path.dirname(setup_script)

            if os.path.exists(mpd_basedir + "/build"):
                desired_file = "%s/%s/%s/%s/BuildInfo/GetPackageBuildInfo.cc" % (
                    mpd_basedir,
                    "build",
                    pkgname,
                    pkgname,
                )
                if os.path.exists(desired_file):
                    pkg_build_infos[pkgname] = parse_buildinfo_file(desired_file)
                else:
                    # print "Unable to find a file with the name %s, will not be able to save build info for %s in the run record" % (desired_file, pkgname)
                    pass

            else:
                print(
                    "No local build subdirectory was found in %s, no build info for %s will be saved in the run record"
                    % (mpd_basedir, pkgname)
                )
                pass

    return pkg_build_infos


def fhicl_writes_root_file(fhicl_string):

    # 17-Apr-2018, KAB: added the MULTILINE flag to get this search to behave as desired.
    # 30-Aug-2018, KAB: added support for RootDAQOutput

    if ("RootOutput" in fhicl_string or "RootDAQOut" in fhicl_string) and re.search(
        r"^\s*fileName\s*:\s*.*\.root", fhicl_string, re.MULTILINE
    ):
        return True
    else:
        return False


def fhiclize_document(filename):

    fhiclized_lines = []

    with open(filename) as inf:
        for line in inf.readlines():
            # Parse any line that's not blank or a comment
            if not re.search(r"^\s*$", line) and not re.search(r"^\s*#.*$", line):
                res = re.search(r"^\s*(\S[^:]*):\s*(\S.*)[\s]", line)
                if res:
                    key = res.group(1)
                    key = "_".join(key.split())
                    key = re.sub(r"[\(\)/]", "_", key)

                    value = res.group(2)
                    value = value.strip(' "')
                    value = value.strip("'")
                    value = value.replace('"', '\\"')

                    fhiclized_lines.append('%s: "%s"' % (key, value))
                else:
                    print(
                        'WARNING: %s not able to FHiCLize the line "%s"'
                        % (fhiclize_document.__name__, line.rstrip())
                    )
            else:
                continue
    return "\n".join(fhiclized_lines)


def get_messagefacility_template_filename():
    if "DAQINTERFACE_MESSAGEFACILITY_FHICL" in os.environ.keys():
        messagefacility_fhicl_filename = os.environ[
            "DAQINTERFACE_MESSAGEFACILITY_FHICL"
        ]
    else:
        messagefacility_fhicl_filename = os.getcwd() + "/MessageFacility.fcl"

    return messagefacility_fhicl_filename


def obtain_messagefacility_fhicl(have_artdaq_mfextensions):

    messagefacility_fhicl_filename = get_messagefacility_template_filename()

    # JCF, 10-25-2018

    # The FHiCL controlling messagefacility messages below is
    # embedded by artdaq within other FHiCL code (see
    # artdaq/DAQdata/configureMessageFacility.cc in artdaq
    # v2_03_03 for details).

    default_contents = """

# This file was automatically generated as %s at %s on host %s, and is
# the default file DAQInterface uses to determine how to modify the
# standard MessageFacility configuration found in artdaq-core
# v3_02_01's configureMessageFacility.cc file. You can edit the
# contents below to change the behavior of how/where MessageFacility
# messages are sent, though keep in mind that this FHiCL will be
# nested inside a table. Or you can use a different file by setting
# the environment variable DAQINTERFACE_MESSAGEFACILITY_FHICL to the
# name of the other file.

udp : { type : "UDP" threshold : "DEBUG"  port : DAQINTERFACE_WILL_OVERWRITE_THIS_WITH_AN_INTEGER_VALUE host : "%s" }

""" % (
        messagefacility_fhicl_filename,
        date_and_time(),
        socket.gethostname(),
        socket.gethostname(),
    )

    if not os.path.exists(messagefacility_fhicl_filename):
        with open(messagefacility_fhicl_filename, "w") as outf_mf:
            outf_mf.write(default_contents)

    processed_messagefacility_fhicl_filename = (
        "/tmp/messagefacility_partition%s_%s.fcl"
        % (os.environ["DAQINTERFACE_PARTITION_NUMBER"], os.environ["USER"])
    )

    with open(messagefacility_fhicl_filename) as inf_mf:
        with open(processed_messagefacility_fhicl_filename, "w") as outf_mf:
            for line in inf_mf.readlines():
                res = re.search(r"^\s*udp", line)
                if not res:
                    outf_mf.write(line)
                elif have_artdaq_mfextensions:
                    outf_mf.write(
                        re.sub(
                            "port\s*:\s*\S+",
                            "port: %d"
                            % (
                                10005
                                + int(os.environ["DAQINTERFACE_PARTITION_NUMBER"])
                                * 1000
                            ),
                            line,
                        )
                    )
                else:  # Note that a completely-empty (i.e., free even of comments) messagefacility fhicl filename will cause an error...
                    outf_mf.write(
                        "\n# udp table for MsgViewer not used since artdaq_mfextensions not available\n"
                    )

    return processed_messagefacility_fhicl_filename


def get_private_networks(host):
    cmd = '/usr/sbin/ifconfig | sed -r -n "s/^\s*inet\s+(192\.168\.\S+|10\.\S+)\s+.*/\\1/p"'

    if not host_is_local(host):
        cmd = "ssh -o BatchMode=yes -x %s '%s'" % (host, cmd)

    lines = Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="UTF-8",
    ).stdout.readlines()
    networks = []

    for line in lines:
        network = line.strip()
        res = re.search(r"^([0-9]+\.[0-9]+\.[0-9]+\.)[0-9]+", network)
        if not res:
            raise Exception(
                'Unexpected result from command "%s"; line "%s" doesn\'t appear to be an address'
                % (cmd, network)
            )
        networks.append(network)

    return networks


def zero_out_last_subnet(network):
    res = re.search(r"^([0-9]+\.[0-9]+\.[0-9]+\.)[0-9]+", network)
    assert res, 'Developer error: proper address not passed to "zero_out_last_subnet"'
    return "%s0" % (res.group(1))


def record_directory_info(recorddir):
    if not os.path.exists(recorddir):
        raise Exception('Directory "%s" doesn\'t exist, exiting...')
    stats = os.stat(recorddir)
    return "inode: %s" % (stats.st_ino)


def get_short_hostname():
    hostname = (
        Popen(
            "hostname -s",
            executable="/bin/bash",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="UTF-8",
        )
        .stdout.readlines()[0]
        .strip()
    )
    return hostname


def main():

    if len(sys.argv) > 1 and sys.argv[1] == "get_commit_info":
        if len(sys.argv) != 5:
            print(
                make_paragraph(
                    'Error: expected four arguments ("get_commit_info", the name of the package (dashes, not underscores), the full pathname of that package\'s git repository whose commit info you want, and the full pathname of the output directory where you want to save the commit info)'
                )
            )
            sys.exit(1)
        pkgname = sys.argv[2]
        gitrepo = sys.argv[3]
        outputdir = sys.argv[4]

        if not os.path.exists(gitrepo):
            print('Error: requested repo "%s" doesn\'t appear to exist' % (gitrepo))
            sys.exit(2)

        if not os.path.exists(outputdir):
            print(
                'Error: requested output directory "%s" doesn\'t appear to exist'
                % (outputdir)
            )
            sys.exit(3)

        filename = "%s/%s" % (outputdir, get_commit_info_filename(pkgname))

        try:
            outf = open(filename, "w")
        except:
            print('Error: problem opening the file "%s" for writing' % (filename))
            sys.exit(4)

        try:
            outf.write(get_commit_info(pkgname, gitrepo))
        except:
            print('Error: problem getting the commit info from "%s"' % (gitrepo))
            sys.exit(5)

        sys.exit(0)

    elif len(sys.argv) > 1 and sys.argv[1] == "record_directory_info":
        if len(sys.argv) != 3:
            print(
                make_paragraph(
                    "Error: expected 1 argument to record_directory_info: the name of an existing run records directory"
                )
            )
            sys.exit(1)
        print(record_directory_info(sys.argv[2]))
        sys.exit(0)

    paragraphed_string_test = False
    msgviewer_check_test = False
    execute_command_in_xterm_test = False
    reformat_fhicl_document_test = False
    bash_unsetup_test = False
    get_commit_info_test = False
    get_build_info_test = False
    table_range_test = False
    get_private_networks_test = False
    enclosing_table_name_test = True
    enclosing_table_range_test = True

    if paragraphed_string_test:
        sample_string = "Set this string to whatever string you want to pass to make_paragraph() for testing purposes"

        paragraphed_string = make_paragraph(sample_string)

        print
        print("Sample string: ")
        print(sample_string)

        print
        print("Paragraphed string: ")
        print(paragraphed_string)

    if msgviewer_check_test:
        if is_msgviewer_running():
            print("A msgviewer appears to be running")
        else:
            print("A msgviewer doesn't appear to be running")

    if execute_command_in_xterm_test:
        execute_command_in_xterm(os.environ["PWD"], "echo Hello world")
        execute_command_in_xterm(
            os.environ["PWD"], "echo You should see an xclock appear; xclock "
        )

    if reformat_fhicl_document_test:
        assert (
            False
        ), "This test is deprecated until function signature is brought up-to-date"
        inputstring = 'mytable: {   this: "and"        that: "and  the other"   }'
        source_filename = (
            Popen(
                "mktemp",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="UTF-8",
            )
            .stdout.readlines()[0]
            .strip()
        )

        # Note the setup string assumes cvmfs is available...
        proddir = "/cvmfs/fermilab.opensciencegrid.org/products/artdaq"
        print("This test assumes that %s is available" % (proddir))

        with open(source_filename, "w") as source_file:
            source_file.write(
                "source %s/setup; setup fhiclcpp v4_05_01 -q prof:e14" % (proddir)
            )

        outputstring = "Not set"
        try:
            outputstring = reformat_fhicl_document(source_filename, inputstring)
        except Exception:
            print("Exception caught")

        os.unlink(source_filename)

        print("Input FHiCL string: ")
        print(inputstring)
        print
        print("Output FHiCL string: ")
        print(outputstring)
        print

    if get_commit_info_test:
        pkgname = "artdaq"
        gitrepo = "/home/jcfree/artdaq-demo_v3_04_01/srcs/artdaq"

        print("Commit info for %s:" % (gitrepo))
        print(get_commit_info(pkgname, gitrepo))

    if get_build_info_test:
        pkgnames = [
            "artdaq-demo",
            "artdaq-core-demo",
            "artdaq",
            "artdaq-utilities",
            "artdaq-core",
        ]
        daq_setup_script = "/home/jcfree/artdaq-demo_v3_04_01/setupARTDAQDEMO"

        pkg_build_infos_dict = get_build_info(pkgnames, daq_setup_script)
        for pkg, buildinfo in pkg_build_infos_dict.items():
            print("%s: %s" % (pkg, buildinfo))

    if table_range_test:

        assert (
            "ARTDAQ_DAQINTERFACE_DIR" in os.environ
        ), "Need to have DAQInterface environment sourced for table_range test"
        filename = "%s/simple_test_config/pdune_swtrig_noRM/DFO.fcl" % (
            os.environ["ARTDAQ_DAQINTERFACE_DIR"]
        )
        print("From file %s:" % (filename))

        with open(filename) as inf:
            inf_contents = inf.read()

            (table_start, table_end) = table_range(inf_contents, "art")
            print("Contents of table: ")
            print(inf_contents[table_start:table_end])

    if get_private_networks_test:
        hosts = ["localhost"]

        for host in hosts:
            private_networks = get_private_networks(host)
            print("%s: " % (host))
            print([network.strip() for network in private_networks])

    if enclosing_table_range_test or enclosing_table_name_test:
        if len(sys.argv) != 3:
            print(
                make_paragraph(
                    "Since at least one of enclosing_table_range_test and enclosing_table_name_test are true, you need to supply the name of a FHiCL file and then a token which is enclosed in a table in the file"
                )
            )
            sys.exit(0)
        filename = sys.argv[1]
        token = sys.argv[2]

        if not os.path.exists(filename):
            raise Exception('Unable to find FHiCL file "%s"' % (filename))

        full_fhicl_blob = open(filename).read()

        if enclosing_table_range_test:
            start, end = enclosing_table_range(full_fhicl_blob, token)

            if start == -1 or end == -1:
                raise Exception(
                    'Uh-oh: unable to find an enclosing table around "%s"' % (token)
                )

            print
            print(
                "Enclosing table range starts at %d and ends at %d. Contents of table are between the =====s"
                % (start, end)
            )
            print(
                "======================================================================"
            )
            print(full_fhicl_blob[start:end])
            print(
                "======================================================================"
            )
            print

        if enclosing_table_name_test:
            tablename = enclosing_table_name(full_fhicl_blob, token)
            print('Name of table enclosing "%s" found to be "%s"' % (token, tablename))


def get_setup_commands(spackdir=None, log_file=None):
    output = []
    if spackdir != None:
        output.append("export SPACK_DISABLE_LOCAL_CONFIG=true")
        if log_file == None:
            output.append(". %s/share/spack/setup-env.sh" % (spackdir))
        else:
            output.append(
                ". %s/share/spack/setup-env.sh >> %s 2>&1" % (spackdir, log_file)
            )
        output.append("spack unload > /dev/null 2>&1")
    return output


def kill_tail_f():
    tail_pids = get_pids(
        "%s.*tail -f %s"
        % (os.environ["DAQINTERFACE_TTY"], os.environ["DAQINTERFACE_LOGFILE"])
    )
    if len(tail_pids) > 0:
        status = Popen(
            "kill %s" % (" ".join(tail_pids)),
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).wait()
        if status != 0:
            print(
                "There was a problem killing \"tail -f\" commands in this terminal; you'll want to do this manually or you'll get confusing output moving forward"
            )


if __name__ == "__main__":
    main()
