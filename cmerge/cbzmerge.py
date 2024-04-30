import os
import os.path as fsp  # file system path
import shutil
import zipfile
from pathlib import Path

import click
import filetype
import rarfile

from .comicinfo import parse_comicinfo
from .util import get_filename_number, listdir_dirs, listdir_files, log, rename_page, safe_remove

ALLOWED_ZIP = [".cbz", ".zip"]
ALLOWED_RAR = [".cbr", ".rar"]
ARCHIVE_EXTENSIONS = [
	*ALLOWED_ZIP,
	*ALLOWED_RAR
	# ".cbt", # tar
	# ".cb7" # 7zip
]

def find_temp_folder():
	base_dir = "temp_merge"
	mod = 0
	temp_dir = base_dir
	while fsp.exists(temp_dir):
		mod += 1
		temp_dir = base_dir + str(mod)
	return temp_dir

# def comics_from_prefix(prefix, workdir="."):
# 	all_comics = comics_in_folder(workdir=workdir)
# 	comics = []
# 	for file_name in all_comics:
# 		if file_name.startswith(prefix):
# 			comics.append(file_name)
# 	return comics


# Passing in a start_idx of <= 0 will cause it to start at the beginning of the folder
# Passing in an end_idx of < 0 will cause it to end at the end of the folder
# Both start_idx and end_idx are inclusive
# Index count starts at 1
# def comics_from_indices(start_idx, end_idx, workdir="."):
# 	all_comics = comics_in_folder(workdir=workdir)
# 	comics = []
# 	comic_idx = 1
# 	for file_name in all_comics:
# 		if start_idx <= comic_idx and (comic_idx <= end_idx or end_idx < 0):
# 			comics.append(file_name)
# 		comic_idx += 1
# 	return comics


# def comics_in_folder(workdir="."):
# 	comics = []
# 	for file_name in os.listdir(workdir):
# 		if Path(file_name).suffix.lower() in ARCHIVE_EXTENSIONS:
# 			comics.append(file_name)
# 	return comics


def flatten_tree(abs_directory):
	"""destructively flattens directory tree to only include files, no folders"""
	file_dump_path = fsp.join(abs_directory, "_dir_files")
	os.mkdir(file_dump_path)

	file_counter = 1
	for path_to_dir, subdir_names, file_names in os.walk(abs_directory, True): # walk to dump all files to 1 folder
		for f in file_names:
			if ".nomedia" in f:
				os.remove(fsp.join(path_to_dir, f))
				file_names.remove(".nomedia")

		if len(subdir_names) == 0 and (abs_directory == path_to_dir):
			break

		for f in file_names: # dump all of current directory's files into it's dump dir
			new_name = fsp.join(path_to_dir, rename_page(file_counter, Path(f).suffix))
			os.rename(fsp.join(path_to_dir, f), fsp.join(path_to_dir, new_name))
			shutil.move(new_name, fsp.join(file_dump_path, f))
			file_counter += 1

	for f in os.listdir(file_dump_path): # move all dumped files into abs_directory
		shutil.move(fsp.join(file_dump_path, f), fsp.join(abs_directory, f))

	for folder in listdir_dirs(abs_directory): # sanity check clean all empty folders
		shutil.rmtree(fsp.join(abs_directory, folder))

class ComicMerge:
	def __init__(
		self,
		output_name,
		comics_to_merge, 
		chunk_ch: None | int = None,
		chunk_mb: None | int = None,
		chapters=False,
		first_chapter: int = 1,
		is_verbose=True,
		workdir="."
	):
		self.output_name = output_name
		if not self.output_name.endswith(".cbz"):
			self.output_name = self.output_name + ".cbz"
		self.comics_to_merge = comics_to_merge
		self.is_verbose = is_verbose
		self.keep_subfolders = chapters

		# self.chunk_ch = chunk_ch
		# self.chunk_mb = chunk_mb
		# self.chuck = chunk_mb is not None or chunk_ch is not None
		# self.flat_page_map: dict[str, list[str]] = {}
		self.first_chapter = first_chapter

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

			folders = os.listdir(self.temp_dir)
			last_chapter_digits = len(str(len(folders)))  # number of digits the last chapter requires
			for i in range(len(folders)):
				folder = folders[i]
				new_name = "Chapter " + str(i + self.first_chapter).zfill(last_chapter_digits + 1)
				
				folder_abs = fsp.join(self.temp_dir, folder)
				for rf in listdir_files(folder_abs):
					file_path = fsp.join(folder_abs, rf)
					if not filetype.is_image(file_path):
						if rf == "ComicInfo.xml":
							chapter_info = parse_comicinfo(file_path)
							if chapter_info.get("Title") is not None:
								new_name = str(chapter_info.get("Title"))
						os.remove(file_path)
			
				os.rename(fsp.join(self.temp_dir, folder), fsp.join(self.temp_dir, new_name))
		else:
			# Flatten file structure (subdirectories mess with some readers)
			files_moved = 1
			for path_to_dir, subdir_names, file_names in os.walk(self.temp_dir, False):
				for file_name in file_names:
					file_path = fsp.join(path_to_dir, file_name)

					if not filetype.is_image(file_path):
						os.remove(file_path)
						continue

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
				for folder in tracked_folders:
					abs_folder = fsp.join(self.temp_dir, folder)
					page_counter = 1
					for fn in listdir_files(abs_folder):
						new_name = rename_page(page_counter, Path(fn).suffix)
						zip_file.write(fsp.join(self.temp_dir, folder, fn), fsp.join(folder, new_name))
						page_counter += 1
		else: # temp_dir > n*k*pages
			files = listdir_files(self.temp_dir)
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

		self._extract_comics(self.comics_to_merge)
		self._tempdir_to_cbz()

		# Clean up temporary folder
		# print("attempting to rm", self.temp_dir)
		shutil.rmtree(self.temp_dir)
		self._log("")
		print("Successfully merged comics into " + self.output_name + "!")
