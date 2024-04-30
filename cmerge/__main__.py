import glob
import os
from pathlib import Path

import click

from .cbzmerge import ALLOWED_EXTENSIONS, ComicMerge, comics_in_folder


@click.command()
@click.argument("output", type=str, required=True)
@click.argument("inputs", type=str, nargs=-1)
@click.option("--folder", "-f", type=click.Path(file_okay=False, exists=True, dir_okay=True), default=os.getcwd(), help="Input folder for comics. If blank, uses current working directory of script.")
@click.option("--range", "-r", "range_", type=click.IntRange(), nargs=2, default=(0, -1), help="Range (start, end) (inclusive, 1-indexed) of comics in folder to merge", )
@click.option("--chapters", "-c", is_flag=True, help="Don't flatten the directory tree, keep subfolders as chapters")
@click.option("--quieter", "-q", is_flag=True, help="Less information regarding the merging progress")
@click.version_option("1.0.0")
@click.help_option("-h", "--help")
def cli(
	output: str,
	inputs: list[str],
	folder: str,
	range_: tuple[int, int] | None,
	chapters: bool,
	quieter: bool, 
):
	print(output, folder, "range", range_)
	comics_to_merge = []
	folder = os.path.abspath(folder)

	if inputs:  # if inputs are provided, use them instead of searching the folder
		for pattern in inputs:
			for file_path in glob.glob(os.path.join(folder, pattern)):
				if Path(file_path).suffix.lower() in ALLOWED_EXTENSIONS:
					comics_to_merge.append(file_path)
	else:
		comics_to_merge = comics_in_folder(workdir=folder)

	if range_ is not None and (range_[0] != 0 and range_[1] != -1): # fallback to range
		start_idx = max(range_[0]-1, 0)
		end_idx = min(len(comics_to_merge), range_[1])
		comics_to_merge = comics_to_merge[start_idx:end_idx]

	if (len(comics_to_merge) == 0):
		print("Found no supported files for merging.")
		quit()

	comic_merge = ComicMerge(output, comics_to_merge, not quieter, chapters, workdir=folder)
	comic_merge.merge()

cli()
