import os
import os.path as fsp  # file system path
import shutil
import zipfile
from pathlib import Path

import click
import filetype
import rarfile
from natsort import natsorted

from .comicinfo import parse_comicinfo
from .util import append_to_fn_pre_ext, listdir_dirs, listdir_files, log, rename_page, safe_remove

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

def rsum_size(path: str):
	"""recursive sum size"""
	return sum(fsp.getsize(f) for f in Path(path).rglob("**/*") if f.is_file())

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

		for f in natsorted(file_names): # dump all of current directory's files into it's dump dir
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
		chunk_mb: None | int = None,
		convert_format: str | None = None,
		chapters=False,
		first_chapter: int = 1,
		is_verbose=True,
		workdir="."
	):
		self.output_name = output_name
		self.orig_output_name = output_name
		if not self.output_name.endswith(".cbz"):
			self.output_name = self.output_name + ".cbz"
		self.comics_to_merge = comics_to_merge
		self.is_verbose = is_verbose

		self.chunk_mb = chunk_mb
		self.first_chapter = first_chapter

		self.convert_format = convert_format
		self.keep_subfolders = chapters

		self.workdir = workdir  # comic location
		self.temp_dir = os.path.abspath(os.path.join(self.workdir, find_temp_folder()))
		print("workdir", workdir)

	def _log(self, msg):
		"""only logs if verbose == True. internal"""
		log(msg, self.is_verbose)

	def _extract_archive(self, archive_fn: str, destination: str, current: int | str, total: int | str):
		"""
		:param archive_fn only filename.ext, no path.  
		:param destination temp folder
		:param current current archive index or custom string message for [current/total]  
		:param total total archive count or custom string message for [current/total]  
		"""
		output_dir = fsp.join(destination, Path(archive_fn).stem)
		os.mkdir(output_dir)
		archive_path = fsp.join(self.workdir, archive_fn)
		archive = None
		if Path(archive_path).suffix.lower() in ALLOWED_RAR:
			archive = rarfile.RarFile(archive_path)
		else:
			archive = zipfile.ZipFile(archive_path)
		
		with click.progressbar(
			archive.infolist(), 
			show_percent=True, 
			show_eta=False, 
			label=f"> extracting [{current+1 if isinstance(current, int) else current}/{total}]", 
			item_show_func=lambda _: archive_fn
		) as tracked_infolist:
			for item in tracked_infolist:
				archive.extract(item, output_dir)
			archive.close()
			flatten_tree(fsp.join(self.workdir, output_dir))
			if self.is_verbose:
				tracked_infolist.label = f"> extracted {archive_fn}"

	def _process_extracted(self, msg = True):
		if self.keep_subfolders:
			if msg:
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
				for file_name in natsorted(file_names):
					file_path = fsp.join(path_to_dir, file_name)

					if not filetype.is_image(file_path):
						os.remove(file_path)
						continue

					ext = os.path.splitext(file_name)[1]
					new_name = rename_page(files_moved, ext)
					shutil.copy(file_path, fsp.join(self.temp_dir, new_name))
					files_moved += 1

				for subdir_name in subdir_names:
					shutil.rmtree(fsp.join(path_to_dir, subdir_name))

		if self.convert_format is not None:
			self._convert_images(self.temp_dir, self.convert_format)
		
	def _convert_images(self, temp_dir: str, img_fmt: str):
		# using pil image library, convert images to either jpeg, png, webp or mozJPEG.
		# use the following conversion rate for quality of each format: jpeg 50 60 70 80, avif 48 51 52 53, webp 55 64 72 82
		

		pass

	def _extract_comics(self, comics_to_extract: list[str]):
		print("started extracting...", self.temp_dir)
			
		for i, file_name in enumerate(comics_to_extract):
			self._extract_archive(file_name, self.temp_dir, i, len(comics_to_extract))
			

	def _tempdir_to_cbz(self):
		zip_file = zipfile.ZipFile(self.output_name, "w", zipfile.ZIP_DEFLATED)

		if self.keep_subfolders: # temp_dir > n*chapter_dir > k*pages
			folders = listdir_dirs(self.temp_dir)
			with click.progressbar(folders, show_percent=True, label="> zipping up", item_show_func=lambda a: f"{a} > {zip_file.filename}") as tracked_folders:
				for folder in tracked_folders:
					abs_folder = fsp.join(self.temp_dir, folder)
					page_counter = 1
					for fn in natsorted(listdir_files(abs_folder)):
						new_name = rename_page(page_counter, Path(fn).suffix)
						zip_file.write(fsp.join(self.temp_dir, folder, fn), fsp.join(folder, new_name))
						page_counter += 1
		else: # temp_dir > n*k*pages
			files = listdir_files(self.temp_dir)
			with click.progressbar(files, show_percent=True, label="> zipping up", item_show_func=lambda a: f"{a} > {zip_file.filename}") as tracked_listdir:
				for fn in tracked_listdir:
					zip_file.write(fsp.join(self.temp_dir, fn), fn)
	
	def merge(self):
		# Remove existing existing output file, if any (we're going to overwrite it anyway)
		safe_remove(self.output_name)
		# self._log("Merging comics " + str(self.comics_to_merge) + " into file " + self.output_name)
		self._log(f"Merging {len(self.comics_to_merge)} archive files into {self.output_name}")
		
		safe_remove(self.temp_dir)
		os.mkdir(self.temp_dir)
		self._extract_comics(self.comics_to_merge)
		self._process_extracted()
		self._tempdir_to_cbz()
		shutil.rmtree(self.temp_dir)

		print("Successfully merged comics into " + self.output_name + "!")

	def size_chunked_merge(self):
		if self.chunk_mb is None:
			raise Exception("use the 'merge' method if not passing in chunk_mb")

		safe_remove(self.output_name)
		for item in os.listdir(self.workdir):
			currp = Path(fsp.join(self.workdir, item))
			if currp.is_dir() and item.startswith("temp_chunk_"):
				shutil.rmtree(currp)

		# self._log("Merging comics " + str(self.comics_to_merge) + " into file " + self.output_name)
		self._log(f"Merging {len(self.comics_to_merge)} archive files into {self.output_name} (chunked by {self.chunk_mb}MB)")

		comics_idx = 0
		chunk = 0
		while comics_idx < len(self.comics_to_merge):
			curr_chap_dir = ""
			self.first_chapter = comics_idx + 1
			chunk_size = 0 # MB
			while chunk_size < self.chunk_mb: # fill chunk until mb limit is hit or we've run out of comics
				self.temp_dir = fsp.abspath(fsp.join(self.workdir, f"temp_chunk_{chunk}"))
				if not fsp.exists(self.temp_dir):
					os.mkdir(self.temp_dir)
				self._extract_archive(self.comics_to_merge[comics_idx], self.temp_dir, str(chunk_size).rjust(len(str(self.chunk_mb)))+"+", f"{self.chunk_mb}MB")
				curr_chap_dir = fsp.join(self.temp_dir, Path(self.comics_to_merge[comics_idx]).stem)
				comics_idx += 1
				chunk_size = rsum_size(self.temp_dir) // (1024**2)
				if comics_idx >= len(self.comics_to_merge): # if we run out of comics, end chunk
					break
			if chunk_size >= self.chunk_mb: # delete 
				shutil.rmtree(curr_chap_dir)
				comics_idx -= 1
			
			print(f"current batch: {rsum_size(self.temp_dir) // (1024**2)}MB ({self.first_chapter}-{comics_idx})")
			self._process_extracted(msg=False)
			self.output_name = append_to_fn_pre_ext(self.orig_output_name, f"-{self.first_chapter}-{comics_idx}")
			self._tempdir_to_cbz()
			shutil.rmtree(self.temp_dir)

			chunk += 1
		
		print("Successfully merged comics into chunks!")