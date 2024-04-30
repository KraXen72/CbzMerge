import os
import os.path as fsp  # file system path
import re
import shutil
import zipfile
from pathlib import Path

import click
import rarfile

# utils to be moved ig

fn_number_pattern = re.compile(r"\d+")

ALLOWED_ZIP = [".cbz", ".zip"]
ALLOWED_RAR = [".cbr", ".rar"]
ALLOWED_EXTENSIONS = [
	*ALLOWED_ZIP,
	*ALLOWED_RAR
	# ".cbt", # tar
	# ".cb7" # 7zip
]

def log(msg, verbose):
	"""only logs if verbose == True. accesible outside"""
	if verbose:
		print(msg)


def safe_remove(file_name):
	if fsp.exists(file_name):
		os.remove(file_name)


def get_filename_number(file_name):
	matches = fn_number_pattern.findall(file_name)
	if len(matches) > 0:
		return matches[-1]
	else:
		return ""


def comics_from_prefix(prefix, workdir="."):
	all_comics = comics_in_folder(workdir=workdir)
	comics = []
	for file_name in all_comics:
		if file_name.startswith(prefix):
			comics.append(file_name)
	return comics


def comics_from_indices(start_idx, end_idx, workdir="."):
	# Passing in a start_idx of <= 0 will cause it to start at the beginning of the folder
	# Passing in an end_idx of < 0 will cause it to end at the end of the folder
	# Both start_idx and end_idx are inclusive
	# Index count starts at 1
	all_comics = comics_in_folder(workdir=workdir)
	comics = []
	comic_idx = 1
	for file_name in all_comics:
		if start_idx <= comic_idx and (comic_idx <= end_idx or end_idx < 0):
			comics.append(file_name)
		comic_idx += 1
	return comics


def comics_in_folder(workdir="."):
	print(workdir)
	comics = []
	# We're not traversing subdirectories because that's a boondoggle
	for file_name in os.listdir(workdir):
		if Path(file_name).suffix.lower() in ALLOWED_EXTENSIONS:
			comics.append(file_name)
	return comics


def find_temp_folder():
	base_dir = "temp_merge"
	mod = 0
	temp_dir = base_dir
	while fsp.exists(temp_dir):
		mod += 1
		temp_dir = base_dir + str(mod)
	return temp_dir

def listdir_files(target: str):
	"""returns relative paths of all files (not directories) in the target directory (shallow)"""
	return [ p for p in os.listdir(target) if fsp.isfile(fsp.join(target, p)) ]

def listdir_dirs(target: str):
	"""returns relative paths of all directories in the target directory (shallow)"""
	return [ p for p in os.listdir(target) if fsp.isdir(fsp.join(target, p)) ]

def rename_page(counter: int | str, ext: str, padding = 5):
	return f"P{str(counter).rjust(padding, "0")}{ext}"


def flatten_tree(abs_directory):
	"""destructively flattens directory tree to only include files, no folders"""
	file_dump_path = fsp.join(abs_directory, "_dir_files")
	os.mkdir(file_dump_path)

	file_counter = 1
	for path_to_dir, subdir_names, file_names in os.walk(abs_directory, True):  # move all files to 1 folder
		for f in file_names:
			if ".nomedia" in f:
				os.remove(fsp.join(path_to_dir, f))
				file_names.remove(".nomedia")

		if len(subdir_names) == 0 and (abs_directory == path_to_dir):
			break

		for f in file_names:
			new_name = fsp.join(path_to_dir, rename_page(file_counter, Path(f).suffix))
			os.rename(fsp.join(path_to_dir, f), fsp.join(path_to_dir, new_name))
			shutil.move(new_name, fsp.join(file_dump_path, f))
			file_counter += 1

	for subdir in os.scandir(abs_directory):  # yeet all other subdirectories
		if subdir.path.endswith("_dir_files"):
			continue
		shutil.rmtree(subdir.path)

	new_path = os.path.split(file_dump_path)[0]
	for f in os.listdir(file_dump_path):
		shutil.move(fsp.join(file_dump_path, f), fsp.join(new_path, f))
	os.rmdir(file_dump_path)


class ComicMerge:
	def __init__(self, output_name, comics_to_merge, is_verbose=True, chapters=False, cbr=False, workdir="."):
		self.output_name = output_name
		if not self.output_name.endswith(".cbz"):
			self.output_name = self.output_name + ".cbz"
		self.comics_to_merge = comics_to_merge
		self.is_verbose = is_verbose
		self.keep_subfolders = chapters
		self.cbr = cbr

		self.workdir = workdir  # comic location
		self.temp_dir = os.path.abspath(os.path.join(self.workdir, find_temp_folder()))
		print("workdir", workdir)

	def _log(self, msg):
		"""only logs if verbose == True. internal"""
		log(msg, self.is_verbose)

	def _extract_archive(self, file_name, destination, idx: int, total: int):
		"""
		file_name = only filename.ext, no path.
		destination = temp folder
		"""
		output_dir = fsp.join(destination, Path(file_name).stem)
		os.mkdir(output_dir)
		archive_path = fsp.join(self.workdir, file_name)
		archive = None
		if Path(archive_path).suffix.lower() in ALLOWED_RAR:
			archive = rarfile.RarFile(archive_path)
		else:
			archive = zipfile.ZipFile(archive_path)
		
		with click.progressbar(
			archive.infolist(), 
			show_percent=True, 
			show_eta=False, 
			label=f"> extracting [{idx+1}/{total}]", 
			item_show_func=lambda _: file_name
		) as tracked_infolist:
			for item in tracked_infolist:
				archive.extract(item, output_dir)
			archive.close()
			flatten_tree(fsp.join(self.workdir, output_dir))
			if self.is_verbose:
				tracked_infolist.label = f"> extracted {file_name}"


	def _extract_comics(self, comics_to_extract):
		print("started extracting...", self.temp_dir)
		first_archive = -1
		last_archive = -1
		for i, file_name in enumerate(comics_to_extract):
			self._extract_archive(file_name, self.temp_dir, i, len(comics_to_extract))
			archive_num = get_filename_number(file_name)
			if i == 0:
				first_archive = archive_num
			if i == len(comics_to_extract) - 1:
				last_archive = archive_num
	
		print(f"first archive: {first_archive}, last archive: {last_archive}")

		if self.keep_subfolders:
			print("keeping subfolders for chapters")
			# rename the folders to something more readable: ch001, ch002 etc.
			folders = os.listdir(self.temp_dir)
			last_chapter_digits = len(str(len(folders)))  # number of digits the last chapter requires
			for i in range(len(folders)):
				folder = folders[i]
				new_name = "ch" + str(i + 1).zfill(last_chapter_digits + 1)
				os.rename(fsp.join(self.temp_dir, folder), fsp.join(self.temp_dir, new_name))
		else:
			# Flatten file structure (subdirectories mess with some readers)
			files_moved = 1
			for path_to_dir, subdir_names, file_names in os.walk(self.temp_dir, False):
				for file_name in file_names:
					file_path = fsp.join(path_to_dir, file_name)
					ext = os.path.splitext(file_name)[1]
					new_name = rename_page(files_moved, ext)
					# log("Renaming & moving " + file_name + " to " + new_name, self.is_verbose)
					shutil.copy(file_path, fsp.join(self.temp_dir, new_name))
					files_moved += 1

				# Deletes all subdirectories (in the end we want a flat structure)
				# This will not affect walking through the rest of the directories,
				# because it is traversed from the bottom up instead of top down
				for subdir_name in subdir_names:
					shutil.rmtree(fsp.join(path_to_dir, subdir_name))

	def _tempdir_to_cbz(self):
		zip_file = zipfile.ZipFile(self.output_name, "w", zipfile.ZIP_DEFLATED)

		if self.keep_subfolders: # temp_dir > n*chapter_dir > k*pages
			folders = listdir_dirs(self.temp_dir)
			with click.progressbar(folders, show_percent=True, label="> zipping up") as tracked_folders:
				page_counter = 1
				for folder in tracked_folders:
					abs_folder = fsp.join(self.temp_dir, folder)
					for fn in listdir_files(abs_folder):
						new_name = rename_page(page_counter, Path(fn).suffix)
						zip_file.write(fsp.join(self.temp_dir, folder, fn), fsp.join(folder, new_name))
						page_counter += 1
		else: # temp_dir > n*k*pages
			files = [ f for f in os.listdir(self.temp_dir) if fsp.isfile(f) ]
			with click.progressbar(files, show_percent=True, label="> zipping up") as tracked_listdir:
				for fn in tracked_listdir:
					zip_file.write(fsp.join(self.temp_dir, fn), fn)
						

	def merge(self):
		# Remove existing existing output file, if any (we're going to overwrite it anyway)
		safe_remove(self.output_name)

		self._log("Merging comics " + str(self.comics_to_merge) + " into file " + self.output_name)

		# Find and create temporary directory
		safe_remove(self.temp_dir)
		os.mkdir(self.temp_dir)

		# TODO doesen't work with -f flag yet
		# TODO chunk splitting support
		# TODO create a indexed chunk folder
		# TODO handle max being lower than 1 zip / negative (check sizes beforehand)
		# TODO properly name the chunks by index (all), range (where possible)
		self._extract_comics(self.comics_to_merge)
		self._tempdir_to_cbz()

		# Clean up temporary folder
		# print("attempting to rm", self.temp_dir)
		shutil.rmtree(self.temp_dir)
		self._log("")
		print("Successfully merged comics into " + self.output_name + "!")
