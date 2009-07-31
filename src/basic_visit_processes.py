import shutil
import re
import os

# Define a visit_directory class to encapsulate processing.
class Visit_directory:
    PREPROC_SCRIPT = '/Data/data1/lab_scripts/preproc_anat.sh '
    CREATE_CONTENTS_SCRIPT='/Data/data1/lab_scripts/create_contents.sh '

    def __init__(self, subid, raw_scans_directory, processed_scans_directory):
        self.subid = subid
        self.raw_scans_directory = raw_scans_directory
        self.processed_scans_directory = processed_scans_directory
        self.working_directory = os.path.join('/tmp/', os.path.basename(raw_scans_directory))

        try:
            self.check_paths()
        except IOError, err:
            print "There was a problem with permissions or paths: " + err
            sys.exit(1)

    # Basic Sanity & Directory Permissions Checking
    def check_paths(self):
        # Ensure that Raw Directory Exists and is Readable
        if not os.path.exists(self.raw_scans_directory):
            raise IOError, "Visit raw directory " + self.raw_scans_directory + " does not exist."
        elif not os.access(self.raw_scans_directory, os.R_OK):
            raise IOError, "Cannot read visit raw directory: " + path

        # Check any paths that will be written to for correct permissions.
        for path in [self.processed_scans_directory]:
            if os.path.exists(path):
                if not os.access(path, os.W_OK): raise IOError, "Cannot write to: " + path
            else: print "Creating " + path + "..."; os.makedirs(path)

    # Create a copy of data on a local, quick disk and unzip all raw data inside.
    def prepare_working_directory(self, working_directory):
        if not os.path.exists(working_directory):
            self.copyAndUnzip(self.raw_scans_directory, working_directory)
        else: print "Temporary working directory " + working_directory + " already exists."

    # Scan the visit and determine what scans occured and need to be processed.
    # Eventually I will work in the sql database to scan that instead of
    # reparsing, but at the moment I'm just using the old bash script to
    # check file counts and scan series descriptions.
    def parse_scans_and_create_directory_index(self):
        index_file_path = self.create_index_file(self.working_directory)
        if not os.path.exists(index_file_path): shutil.copy(index_file_path, self.raw_scans_directory)

    # Creates and executes the old-school shell command for walking through dicoms and extracting 
    # series descriptions and counts to create an index text file of scans in a visit.
    def create_index_file(self, directory_to_scan, filename = None):
        if not filename: filename = 'anat_list_' + self.subid + '.txt'
        index_file_path = os.path.join(directory_to_scan, filename)
        cmd = self.CREATE_CONTENTS_SCRIPT + " %s %s" % (directory_to_scan, index_file_path)
        os.system(cmd)
        #os.system("lpr " + anat_index_file)
        return os.path.abspath(index_file_path)
    
    # Run basic preprocessing.  This currently just runs an old shell script, but will be
    # updated to integrate with our imaging database and yaml processing configuration.
    def preprocess_each_scan(self):
        for recon_type in ['anat']:
            if not os.path.exists(os.path.join(self.processed_scans_directory, recon_type)):
                self.recon(recon_type)

    # Compiles Shell Command for reconstruction with preproc_anat.sh and runs it.
    def recon(self, recon_type, prefix = None, output_directory = None):
        if not output_directory:
            output_directory = os.path.join(self.processed_scans_directory, recon_type)

        cmd = self.PREPROC_SCRIPT + ' %s %s %s %s ' % (self.working_directory, output_directory, prefix or self.subid, recon_type)
        print cmd
        os.system(cmd)

    # Cleanup
    def tidy_up(self):
        print "Tidying Up Visit Directories for " + self.subid
        self.tidy_up_raw_scans_directory()
        self.tidy_up_working_directory()

    # Zip All dicoms in the Raw Directory
    def tidy_up_raw_scans_directory(self):
        try:
            if not os.access(self.raw_scans_directory, os.W_OK):
                raise IOError, "Error: Raw directory " + self.raw_scans_directory + " must be writable to zip files.  Try again as the raw user."
            else: self.zip(self.raw_scans_directory)
        except IOError, err:
            print err

    # Creates and executes a shell find command to recursively zip a directory, ignoring select small files
    def zip(self, directory_to_zip):
        print "Zipping " + directory_to_zip
        os.system("find " + directory_to_zip + " -type f -not -name '*.txt' -not -name '*.yaml' -not -name '*.tar' -name '*' -exec bzip2 {} \;")


    # Remove the Working Directory
    def tidy_up_working_directory(self):
        print "Tidying up temporary working directory " + self.working_directory
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
