import shutil
import re
import os

# Define a visit_directory class to encapsulate processing.
class Visit_directory:
    PREPROC_SCRIPT = '/Data/data1/lab_scripts/preproc_anat.sh '
    CREATE_CONTENTS_SCRIPT='/Data/data1/lab_scripts/create_contents.sh '
    DEFAULT_COOKIE = 'study_info_cookie.py'

    def __init__(self, subid, raw_scans_directory, processed_scans_directory):
        self.subid = subid
        self.raw_scans_directory = raw_scans_directory
        self.processed_scans_directory = processed_scans_directory
        self.working_directory = os.path.join('/tmp/', os.path.basename(raw_scans_directory))

        self.check_paths()

    def check_paths(self):
        # Raw Directory Must Exist and be Readable
        if not os.path.exists(self.raw_scans_directory):
            raise IOError, "Visit raw directory " + self.raw_scans_directory + " does not exist."
        elif not os.access(self.raw_scans_directory, os.R_OK):
            raise IOError, "Cannot read visit raw directory: " + path

        # Check any pahts that will be written to for correct permissions.
        for path in [self.processed_scans_directory]:
            if os.path.exists(path):
                if not os.access(path, os.W_OK): raise IOError, "Cannot write to: " + path

    def check_preprocessed_scans_directory(self):
        if not os.exists(self.processed_scans_directory):
            print "Creating Processed Scans Directory " + path + "..."; os.makedirs(path)
        elif not os.access(self.processed_scans_directory, os.W_OK):
            raise IOError, "Cannot write to " + self.processed_scans_directory

    # Create a copy of data on a local, quick disk and unzip all raw data inside.
    def prepare_working_directory(self, working_directory):
        if not os.path.exists(working_directory):
            self.copyAndUnzip(self.raw_scans_directory, working_directory)
        else: print "Temporary working directory " + working_directory + "already exists."

    # Figure out what scans are included in the visit.
    # Eventually I will work in the sql database to scan that instead of
    # reparsing, but at the moment I'm just using the old bash script to
    # check file counts and scan series descriptions.
    def parse_scans_and_create_directory_index(self):
        index_file_path = self.create_index_file(self.working_directory)
        if not os.path.exists(index_file_path): shutil.copy(index_file_path, self.raw_scans_directory)

    def preprocess_each_scan(self):
        for recon_type in ['anat', 'fmri']:
            if not os.path.exists(os.path.join(self.processed_scans_directory, recon_type)):
                self.recon(recon_type)

    def recon(self, recon_type, prefix = None, output_directory = None):
        if not output_directory:
            output_directory = os.path.join(self.processed_scans_directory, recon_type)

        cmd = self.PREPROC_SCRIPT + ' %s %s %s %s ' % (self.working_directory, output_directory, prefix or self.subid, recon_type)
        print cmd
        os.system(cmd)

    # Cleanup
    def tidy_up(self):
        self.tidy_up_raw_scans_directory
        self.tidy_up_working_directory

    # Zip All dicoms in the Raw Directory
    def tidy_up_raw_scans_directory(self):
        try:
            if not os.access(self.raw_scans_directory, os.W_OK):
                raise IOError, "Raw directory " + path + " must be writable to zip files.  Try again as the raw user."
            else: self.zip(self.anatomicals_directory)
        except IOError, msg:
            print msg


    # Remove the Working Directory
    def tidy_up_working_directory(self):
        shutil.rmtree(self.working_directory)

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

    def create_index_file(self, directory_to_scan, filename = None):
        if not filename: filename = 'anat_list_' + self.subid + '.txt'
        index_file_path = os.path.join(directory_to_scan, filename)
        cmd = self.CREATE_CONTENTS_SCRIPT + " %s %s" % (directory_to_scan, index_file_path)
        os.system(cmd)
        #os.system("lpr " + anat_index_file)
        return os.path.abspath(index_file_path)

    def zip(self, directory_to_zip):
        print "Zipping " + directory_to_zip
        os.system("find " + directory_to_zip + " -type f -not -name '*.txt' -not -name '*.yaml' -not -name '*.tar' -name '*' -exec bzip2 {} \;")

