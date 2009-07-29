#!/usr/bin/env python
''' TransferRawFiles.py copies Imaging Scans from remote scanners and runs default processing after the copy.'''

from optparse import OptionParser
import sys, os
import shutil
import re
import glob
from basic_visit_processes import Visit_directory

class TransferTask:
    # Initialize Vars
    process_pool=set()
    study_vars={'raw_dir':None, 'recon_anat_dir': None, 'recon_fmri_cmd': None}
    PREPROC_SCRIPT = '/Data/data1/lab_scripts/preproc_anat.sh '
    CREATE_CONTENTS_SCRIPT='/Data/data1/lab_scripts/create_contents.sh '
    DEFAULT_COOKIE = 'study_info_cookie.py'

    def __init__(self, command_line_args = sys.argv[1:]):
        # Argument Parser
        usage="%prog [options] : Copies Imaging Scans from remote scanners and runs default processing after the copy."
        parser = OptionParser(usage=usage)
        parser.add_option("--subid", "--for", help="Subject Id to use in reconstruction (i.e. 2532)")
        parser.add_option("--remote_location", "--from", help="Source location (user@host:~/sourceDirectory) to transfer. ex; sdc@zoot:~/DICOM/6944_*")
        parser.add_option("--to", help="Destination directory for transfer (ex: /Data/vtrak1/raw/wrap140/2532")
        parser.add_option("--in_study", help="Path to study cookie.", default=False)
        
        if not len(command_line_args) >= 1:
            parser.print_help()
            sys.exit()

        (self.options, args) = parser.parse_args(command_line_args)
            

        self.local_directory, self.subid, self.study_vars['raw_dir'], self.user, self.host, self.remote_directory = self.parse_command_line()

        # Parse the Study Info Cookie
        try:
            if self.options.in_study: cookie_file = self.options.in_study
            else: cookie_file = os.path.join(self.study_vars['raw_dir'], self.DEFAULT_COOKIE)
            self.study_vars['recon_anat_dir'], self.study_vars['recon_fmri_cmd'] = self.parse_cookie(cookie_file)
        except IOError as err:
            print err.args

    # Parses the command line to determine variables needed for transfer and processing.
    # Returns user, host and remote directory as three strings.
    def parse_command_line(self):

        local_directory = self.options.to
        subid = self.options.subid
        raw_dir=os.path.dirname(self.options.to)
        
        user, rest = self.options.remote_location.split('@')
        host, remote_directory = rest.split(':')

        return local_directory, subid, raw_dir, user, host, remote_directory


    # Returns variables about a study from the info cookie in its raw directory.
    def parse_cookie(self, cookie_file):
        if os.path.exists(cookie_file):
            study_variables = []
            cookie = open(cookie_file, 'r')
            exec(cookie.read())
            cookie.close()
            #study_variables['study_recon_anat_dir'] = study_recon_anat_dir
            #study_variables['study_recon_fmri_cmd'] = study_recon_fmri_cmd
            return study_recon_anat_dir, study_recon_fmri_cmd
        else: raise IOError('No Study Cookie Found')

    def set_process_pool(self, study_vars):
        # Check Study Variables
        if study_vars['recon_anat_dir']: self.process_pool.add('doAnatRecon')
        #if study_vars['recon_fmri_dir']: self.process_pool.add('doFmriRecon')

    def check_paths(self):
        # Check Host and Location
        if 'tezpur' in self.host: self.location='wais'; self.anatomicals_directory = os.path.join(self.local_directory,'dicoms');
        elif 'zoot' in self.host: self.location='uwmr'; self.anatomicals_directory = self.local_directory
        else: raise StandardError('RemoteHost Not Recognized')

        # Check Local Directory
        if os.path.exists(self.local_directory):
            print 'The local directory ' + self.local_directory + ' already exists.'
            while True:
                print 'Skip transfer, overwrite local dir or cancel? < skip | overwrite | cancel > '
                input = sys.stdin.readline().strip()
                if input in ['skip', 'overwrite', 'cancel']: break

            if input == 'skip': print "Skipping..."
            elif input == 'overwrite': shutil.rmtree(self.local_directory)
            elif input == 'cancel': sys.exit(1)
        else: self.process_pool |= set(['doTransfer', 'doCreateIndexFile'])

    def transfer(self):
        if self.host=='zoot' and 'miho' not in os.getenv('HOSTNAME'):
            errmsg = """
            - Script Cannot Execute -
            You may only transfer files from zoot using Miho due to firewall rules.
            Please ssh onto Miho and try again."""
            raise StandardError(errmsg)

        # Transfer Physiology
        if self.host=='zoot':
            os.system("scp %s@%s:/var/ftp/pub/*%s* %s" % (self.user, self.host, self.subid, '/tmp/'))

        # Transfer Remote Directory
        os.system("scp -r %s %s" % (self.options.remote_location, self.local_directory))

        if not os.path.exists(self.local_directory):
            raise IOError("Error During Transfer.  You either have typed in the remote directory incorrectly, it doesn't exist, or you have a permissions error." % (self.local_directory))

        # Move Physiology into Anatomicals Directory
        physiology_tar_file = glob.glob(os.path.join('/tmp', self.subid + '*'))[0]
        shutil.move(physiology_tar_file, self.anatomicals_directory)


    ## Copy a Directory Tree and decompress any zipped images.
    #  Used to create a local copy of unziped raw data.
    #  Raises an Error if the Destination directory exists.
    def copyAndUnzip(self, src, dst):
        def ignoreFiles(dir, files):
            if dir != src: return []
            matcher = re.compile("^((\d\d\d)|[sS]\d).*")
            matches = [f for f in files if matcher.match(f)]
            ignored = list(set(files) - set(matches))
            print "Ignoring ", ignored
            return ignored

        src = os.path.abspath(src)
        dst = os.path.abspath(dst)
        print "Copying directory " + src + " to temporary location: " + dst
        if os.path.exists(dst):
            # shutil.copytree will not overwrite directories, so the destination directory cannot exist.
            raise IOError("THE DESTINATION DIRECTORY CANNOT EXIST.  Program terminating.")
        shutil.copytree(src, dst, True, ignoreFiles)
        for (path, dirnames, filenames) in os.walk(dst):
            for f in filenames:
                file = os.path.join(path, f)
                if file.endswith(".bz2"):
                    os.system("bunzip2 %s" % (file,))

def main():

    t = TransferTask()
    t.set_process_pool(t.study_vars)
    t.check_paths()

    if 'doTransfer' in t.process_pool: t.transfer()

    if 'doCreateIndexFile' or 'doAnatRecon' in t.process_pool:
        visitdir = Visit_directory(subid, t.anatomicals_directory, os.path.join(t.study_vars['recon_anat_dir'], t.subid))
        visitdir.prepare_working_directory(visitdir.working_directory)
        if 'doCreateIndexFile' in t.process_pool: visitdir.parse_scans_and_create_directory_index()
        if 'doAnatRecon' in t.process_pool: visitdir.preprocess_each_scan()
        visitdir.tidy_up()


if __name__ == "__main__":
    main()
    

