#!/usr/bin/env python
''' TransferRawFiles.py copies Imaging Scans from remote scanners and runs default processing after the copy.'''

from optparse import OptionParser
import sys
import os
from shutil import rmtree

doPHYS = False; doTRANSFER = True; doCREATEINDEXFILE = True; doANATRECON = False; doFMRIRECON = False; doFMRIPIPE = False
DEFAULT_COOKIE = 'study_info_cookie.py'
study_raw_dir, study_recon_anat_dir, study_recon_fmri_dir, study_fmri_cookie, waisman_info_file = (None, None, None, None, None)

parser = OptionParser(usage="Copies Imaging Scans from remote scanners and runs default processing after the copy.")

parser.add_option("--subid", "--for", help="Subject Id to use in reconstruction (i.e. 2532)")
parser.add_option("--remote_location", "--from", help="Source location (user@host:~/sourceDirectory) to transfer. ex; sdc@zoot:~/DICOM/6944_*")
parser.add_option("--to", help="Destination directory for transfer (ex: /Data/vtrak1/raw/wrap140/2532")
parser.add_option("--in_study", help="Path to study cookie.", default=False)
(options, args) = parser.parse_args()


local_directory = options.to
subid = options.subid
study_raw_dir = os.path.dirname(options.to)

if options.in_study:
    cookie_file = options.in_study
else: cookie_file = os.path.join(study_raw_dir, DEFAULT_COOKIE)

if os.path.exists(cookie_file):
    cookie = open(cookie_file, 'r')
    exec(cookie.read())
    cookie.close()
else: print "Info: No Study Cookie Found."


# Check Study Variables
if study_recon_anat_dir: doANATRECON = True
if study_recon_fmri_dir: doFMRIRECON = True
if study_fmri_cookie: doFMRIPIPE = True

user, rest = options.remote_location.split('@')
host, remote_directory = rest.split(':')

if host=='zoot' and 'miho' not in os.getenv('HOSTNAME'):
    print "SCRIPT CANNOT EXECUTE:"
    print "You may only transfer files from zoot using Miho due to firewall rules."
    print "Please ssh onto Miho and try again."
    sys.exit(1)

# Check Host and Location
if 'tezpur' in host: 
    location='wais'; isZipped = True
    if os.path.islink(os.path.join(local_directory, 'anatomicals')):
      anatomicals_directory = os.path.join(local_directory,'dicoms')
    else:
      anatomicals_directory = os.path.join(local_directory,'anatomicals')
    waisman_info_file = os.path.join(local_directory, 'info.txt')
elif 'zoot' in host: 
    location='uwmr'; isZipped = False; anatomicals_directory = local_directory
else: sys.exit(1)

# Check Local Directory
if os.path.exists(local_directory):
    print 'The local directory ' + local_directory + ' already exists.'
    while True:
        print 'Skip transfer, overwrite local dir or cancel? < skip | overwrite | cancel > '
        input = sys.stdin.readline().strip()
        if input in ['skip', 'overwrite', 'cancel']: break

    if input == 'skip': doTRANSFER=False; doCREATEINDEXFILE = False
    elif input == 'overwrite': rmtree(local_directory)
    elif input == 'cancel': sys.exit(1)

# Begin Processing

# 1. Prepare DTI (Implement Later)

# 2. SCP Subject's Raw Directory to Vtrak.
if doTRANSFER:
    #cmd = "scp -r %s %s" % (options.remote_location, local_directory)
    os.system("scp -r %s %s" % (options.remote_location, local_directory))

    if not os.path.exists(local_directory):
        print "TRANSFER CANCELLED.  Local Directory %s could not be created." % (local_directory,)
        sys.exit(1)

# 3. Check DTI (File Count) (Implement Later)

# 4. Unzip files to allow processing.
if isZipped:
    print "Unzipping " + anatomicals_directory
    os.system("find " + anatomicals_directory + " -name '*.bz2' -exec bunzip2 {} \;")
    isZipped = False

# 5. Create Anatdirs text file.
if doCREATEINDEXFILE:
    anat_index_file = os.path.join(anatomicals_directory, "anat_list_" + subid + ".txt")
    cmd = "create_contents.sh %s %s" % (anatomicals_directory, anat_index_file)
    os.system(cmd)
    os.system("lpr " + anat_index_file)
    
    if waisman_info_file:                                 # Check if path has been set.
        if os.path.exists(waisman_info_file):             # Check if path points to a valid file.
            print os.system("lpr " + waisman_info_file)

# 6. Reconstruct Anatomical Images.
if doANATRECON:
    cmd = "preproc_anat.sh %s %s %s anat" % (anatomicals_directory, os.path.join(study_recon_anat_dir, subid), subid)
    os.system(cmd)

# 7. Reconstruct Functional Images.
if doFMRIRECON:
    cmd = "preproc_anat.sh %s %s %s fmri" % (anatomicals_directory, os.path.join(study_recon_fmri_dir, subid), subid)
    os.system(cmd)

# 8. Transfer Physiological Data from the Hospital.
if doPHYS:
    cmd = "scp %s@%s:/var/ftp/pub/*%s* %s" % (user, host, subid, anatomicals_directory)

# 9. Run Functional Pipeline
if doFMRIPIPE:
    cmd = "/Data/home/erik/pipeline_dev/study_wrappers/preproc.sh %s %s" % (subid, study_fmri_cookie)
    os.system(cmd)

# 10. Cleanup
if not isZipped:
    print "Zipping " + anatomicals_directory
    os.system("find " + anatomicals_directory + " -type f -not -name '*.txt' -not -name '*.yaml' -name '*' -exec bzip2 {} \;")
