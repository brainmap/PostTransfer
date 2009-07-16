#!/usr/bin/env python

import unittest
from TransferRawFiles2 import *

class TestTransferOptions(unittest.TestCase):
	def setUp(self):
		self.t = TransferTask("--from sdc@zoot:/var/ftp/pub/7423_11032008 --to /Data/vtrak1/raw/9000/gallagher_pd/pd001_7423_11032008 --for pd001 --in_study ~/NetBeansProjects/PostTransfer/src/study_info_cookie.py".split(" "))

	def testOptions(self):
		self.assertEqual(self.t.local_directory,"/Data/vtrak1/raw/9000/gallagher_pd/pd001_7423_11032008")
		self.assertEqual(self.t.subid, "pd001")
		self.assertEqual(self.t.study_vars['raw_dir'], "/Data/vtrak1/raw/9000/gallagher_pd")
		self.assertEqual(self.t.user, "sdc")
		self.assertEqual(self.t.host, "zoot")
		self.assertEqual(self.t.remote_directory, "/var/ftp/pub/7423_11032008")

	def testCookieParser(self):
		self.assertRaises(IOError, self.t.parse_cookie, '/Bad/Path/To/Cookie.py')
		self.t.study_vars = self.t.parse_cookie('study_info_cookie.py')
		self.assertEqual(self.t.study_vars['study_recon_anat_dir'], "/Data/vtrak1/preprocessed/visits/gallagher_pd")
		self.assertEqual(self.t.study_vars['study_recon_fmri_cmd'], "/Data/vtrak1/preprocessed/progs/gallagher_pd/preproc-gallagher_pd.visit1.py")

if __name__ == '__main__':
	unittest.main()