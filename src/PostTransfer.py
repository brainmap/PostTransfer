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
# including Subject ID, Raw (Input) Dir and Processed (Output) Dir
def parse_arguments(command_line_args):
    process_variables = {}
    parser = create_argument_parser()

    if not len(command_line_args) >= 1:
        parser.print_help()
        sys.exit()
    (options, args) = parser.parse_args(command_line_args)

    process_variables['subid'] = options.subid
    process_variables['raw_scans_directory'] = os.path.dirname(options.raw_dir)
    process_variables['processed_scans_directory'] = os.path.abspath(options.processed_dir)

    return process_variables

def require_python_version(version_number):
    if sys.version < version_number:
        print 'Newer version of Python required (at least 2.6) required for shutil ignorefiles copy functionality.'
        sys.exit(1)

# Run Processing on an entire Raw Visit Directory, using default path structure
# This is only useful for gluing dicoms together into 3D Nifti volumes at the
# moment, but I will be adding functionality to it as a processing framework
# in order to call "real" processing on various image types in the future.
def main():
    require_python_version('2.6')
    process_variables = parse_arguments(sys.argv[1:])
    visitdir = Visit_directory(process_variables['subid'], process_variables['raw_scans_directory'], process_variables['processed_scans_directory'])
    visitdir.prepare_working_directory(visitdir.working_directory)
    visitdir.parse_scans_and_create_directory_index()
    visitdir.preprocess_each_scan()
    visitdir.tidy_up()

if __name__ == "__main__":
    main()
