import os
import os.path as fsp  # file system path
import re
from pathlib import Path

fn_number_pattern = re.compile(r"\d+")

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

def listdir_files(target: str):
	"""returns relative paths of all files (not directories) in the target directory (shallow)"""
	return [ p for p in os.listdir(target) if fsp.isfile(fsp.join(target, p)) ]

def listdir_dirs(target: str):
	"""returns relative paths of all directories in the target directory (shallow)"""
	return [ p for p in os.listdir(target) if fsp.isdir(fsp.join(target, p)) ]

def rename_page(counter: int | str, ext: str, padding = 5):
	return f"P{str(counter).rjust(padding, "0")}{ext}"

def append_to_fn_pre_ext(fn: str, append: str):
	if "." not in fn:
		return fn + append
	else:
		fnp = Path(fn)
		return f"{fnp.stem}{append}{fnp.suffix}"