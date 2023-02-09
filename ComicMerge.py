import os
import shutil
import zipfile

# utils to be moved ig

def log(msg, verbose):
	"""only logs if verbose == True. accesible outside"""
	if verbose:
		print(msg)

def safe_remove_file(file_name):
	if os.path.exists(file_name):
		os.remove(file_name)

class ComicMerge:
	def __init__(self, output_name, comics_to_merge, is_verbose=True, chapters=False, workdir='.'):
		self.output_name = output_name
		if not self.output_name.endswith(".cbz"):
			self.output_name = self.output_name + ".cbz"
		self.comics_to_merge = comics_to_merge
		self.is_verbose = is_verbose
		self.keep_subfolders = chapters
		self.workdir = workdir

	def _log(self, msg):
		"""only logs if verbose == True. internal"""
		log(msg, self.is_verbose)

	def _flatten_tree(self):
		"""flattens"""

	def _extract_cbz(self, file_name, destination, verbose):
		"""
		file_name = only filename.ext, no path.
		destination = temp folder
		"""
		# print("ecbz", self.workdir, file_name, destination)
		output_dir = os.path.join(destination, os.path.splitext(file_name)[0])
		os.mkdir(output_dir)
		log('Unzipping ' + file_name, verbose)

		zip_file = zipfile.ZipFile(os.path.join(self.workdir, file_name))
		zip_file.extractall(output_dir)
		zip_file.close()
		# TODO deeply extract

	def _extract_comics(self, comics_to_extract, temp_dir):
		for file_name in comics_to_extract:
			ComicMerge._extract_cbz(self, file_name, temp_dir, self.is_verbose)

		if self.keep_subfolders:
			print("keeping subfolders for chapters")
			# rename the folders to something more readable: ch001, ch002 etc.
			folders = os.listdir(temp_dir)
			last_chapter_digits = len(str(
				len(folders)))  # number of digits the last chapter requires
			for i in range(len(folders)):
				folder = folders[i]
				new_name = "ch" + str(i + 1).zfill(last_chapter_digits + 1)
				os.rename(os.path.join(temp_dir, folder),
						  os.path.join(temp_dir, new_name))
		else:
			# Flatten file structure (subdirectories mess with some readers)
			files_moved = 1
			for path_to_dir, subdir_names, file_names in os.walk(temp_dir, False):
				for file_name in file_names:
					file_path = os.path.join(path_to_dir, file_name)
					ext = os.path.splitext(file_name)[1]
					new_name = 'P' + str(files_moved).rjust(5, '0') + ext
					log('Renaming & moving ' + file_name + ' to ' + new_name, self.is_verbose)
					shutil.copy(file_path, os.path.join(temp_dir, new_name))
					files_moved += 1

				# Deletes all subdirectories (in the end we want a flat structure)
				# This will not affect walking through the rest of the directories,
				# because it is traversed from the bottom up instead of top down
				for subdir_name in subdir_names:
					shutil.rmtree(os.path.join(path_to_dir, subdir_name))

	def _make_cbz_from_dir(self, temp_dir):
		self._log('Initializing cbz ' + self.output_name)

		if self.keep_subfolders:
			zip_file = zipfile.ZipFile(self.output_name, 'w', zipfile.ZIP_DEFLATED)
			self._log('Adding chapter folders to cbz ' + self.output_name)

			add_count = 0
			for path_to_dir, subdir_names, file_names in os.walk(temp_dir):
				page_counter = 1
				for file_name in file_names:
					file_path = os.path.join(path_to_dir, file_name)
					head, tail = os.path.split(file_path)

					ext = os.path.splitext(file_name)[1]
					new_name = 'P' + str(page_counter).rjust(5, '0') + ext
					zip_file.write(
						file_path,
						os.path.join(os.path.split(head)[1], new_name))
					add_count += 1
					page_counter += 1
					if add_count % 10 == 0:
						print('> ' + str(add_count) + ' files added.', end='\r')
		else:
			zip_file = zipfile.ZipFile(self.output_name, 'w', zipfile.ZIP_DEFLATED)
			self._log('Adding files to cbz ' + self.output_name)
			add_count = 0
			for path_to_dir, subdir_names, file_names in os.walk(temp_dir):
				for file_name in file_names:
					file_path = os.path.join(path_to_dir, file_name)
					zip_file.write(file_path, os.path.split(file_path)[1])
					add_count += 1
					if add_count % 10 == 0:
						print('> ' + str(add_count) + ' files added.', end='\r')

	def _find_temp_folder():
		base_dir = 'temp_merge'
		mod = 0
		temp_dir = base_dir
		while os.path.exists(temp_dir):
			mod += 1
			temp_dir = base_dir + str(mod)
		return temp_dir

	@staticmethod
	def comics_from_indices(start_idx, end_idx, workdir='.'):
		# Passing in a start_idx of <= 0 will cause it to start at the beginning of the folder
		# Passing in an end_idx of < 0 will cause it to end at the end of the folder
		# Both start_idx and end_idx are inclusive
		# Index count starts at 1
		all_comics = ComicMerge.comics_in_folder(workdir=workdir)
		comics = []
		comic_idx = 1
		for file_name in all_comics:
			if start_idx <= comic_idx and (comic_idx <= end_idx
										   or end_idx < 0):
				comics.append(file_name)
			comic_idx += 1
		return comics

	@staticmethod
	def comics_from_prefix(prefix, workdir='.'):
		all_comics = ComicMerge.comics_in_folder(workdir=workdir)
		comics = []
		for file_name in all_comics:
			if file_name.startswith(prefix):
				comics.append(file_name)
		return comics

	@staticmethod
	def comics_in_folder(workdir='.'):
		comics = []
		# We're not traversing subdirectories because that's a boondoggle
		# TODO implement ^^
		for file_name in os.listdir(workdir):
			if os.path.splitext(file_name)[1] == '.cbz':
				comics.append(file_name)
		return comics

	def merge(self):
		# Remove existing existing output file, if any (we're going to overwrite it anyway)
		safe_remove_file(self.output_name)

		self._log('Merging comics ' + str(self.comics_to_merge) + ' into file ' + self.output_name)

		# Find and create temporary directory
		temp_dir = self._find_temp_folder()
		os.mkdir(temp_dir)

		#FIXME doesen't work with -f flag yet
		self._extract_comics(self.comics_to_merge, temp_dir)
		self._make_cbz_from_dir(temp_dir)

		# Clean up temporary folder
		shutil.rmtree(temp_dir)
		self._log('')
		print('Successfully merged comics into ' + self.output_name + '!')