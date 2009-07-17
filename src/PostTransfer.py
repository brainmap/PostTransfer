#!/usr/bin/env python

import sys
import os
from optparse import OptionParser
from basic_visit_processes import Visit_directory


# Create the Arguments/Options Parser
# Returns an Options Parser that understands Subject ID,
# Raw (Input) Dir and Processed (Output) Dir
def create_argument_parser():
    # Argument Parser
    usage="%prog [options] : Runs simple, default processing on Visit Directories."
    parser = OptionParser(usage=usage)
    parser.add_option("--subid", "--for", help="Subject Id to use in reconstruction (i.e. 2532)")
    parser.add_option("--raw_dir", "-r", help="Raw Visit Directory")
    parser.add_option("--processed_dir", "-p", help="Processed Visit Directory")
    return parser

# Handles parsing command line arguments related to high-level reconstruction,
# and returns a hash including Subject ID, Raw (Input) Dir and Processed (Output) Dir
def parse_arguments(command_line_args):
    arguments = {}
    parser = create_argument_parser()

    if not len(command_line_args) >= 1:
        parser.print_help()
        sys.exit()
    (options, args) = parser.parse_args(command_line_args)

    arguments['subid'] = options.subid
    arguments['raw_scans_directory'] = os.path.abspath(options.raw_dir)
    arguments['processed_scans_directory'] = os.path.abspath(options.processed_dir)

    return arguments

# Exit unless current python version matches or is higher than required version.
# You can pass in an explanatory message if you like.
def require_python_version(version_number, error_msg = "Newer version of Python required."):
    if sys.version < version_number:
        print "Python version " + version_number + " is required, but it is currently " + sys.version
        print error_msg
        sys.exit(1)

# Run Processing on an entire Raw Visit Directory, using default path structure
# This is only useful for gluing dicoms together into 3D Nifti volumes at the
# moment, but I will be adding functionality to it as a processing framework
# in order to call "real" processing on various image types in the future.
def main():
    require_python_version('2.6', 'Version 2.6 is required for shutil ignorefiles copy functionality.')
    arguments = parse_arguments(sys.argv[1:])
    visitdir = Visit_directory(arguments['subid'], arguments['raw_scans_directory'], arguments['processed_scans_directory'])
    visitdir.prepare_working_directory(visitdir.working_directory)
    visitdir.parse_scans_and_create_directory_index()
    visitdir.preprocess_each_scan()
    visitdir.tidy_up()

if __name__ == "__main__":
    main()
