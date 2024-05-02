import glob
import os
from pathlib import Path

import click
from natsort import natsorted  # pyright: ignore

from .cbzmerge import ARCHIVE_EXTENSIONS, ComicMerge


@click.command()
@click.argument("output", type=str, nargs=1)
@click.option("--folder", "-f", type=click.Path(file_okay=False, exists=True, dir_okay=True), default=os.getcwd(), help="Input folder for comics. If blank, uses current working directory of script.")
@click.option("--range", "-r", "range_", type=click.IntRange(), nargs=2, default=(0, -1), help="Range (start, end) (inclusive, 1-indexed) of comics in folder to merge")
@click.option("--chunk-ch", "-s", type=int, help="Autosplit into chunks by number of chapters.")
@click.option("--chunk-mb", "-m", type=int, help="Autosplit into chunks by max MB per chunk.")
@click.option("--chapters", "-c", is_flag=True, help="Don't flatten the directory tree, keep subfolders as chapters")
@click.option("--quieter", "-q", is_flag=True, help="Less information regarding the merging progress")
@click.option("--in", "-i", "input_glob", multiple=True,type=str, help=f"Input glob (relative to --folder). allowed extensions: {", ".join(ARCHIVE_EXTENSIONS)}. use -i='*.cbz' or w/e in powershell.")
@click.version_option("1.0.0")
@click.help_option("-h", "--help")
def cli(
	output: str,
	folder: str,
	range_: tuple[int, int] | None,
	chunk_ch: int | None,
	chunk_mb: int | None,
	chapters: bool,
	quieter: bool, 
	input_glob: list[str] | str = [],
):
	comics_to_merge: list[str] = []
	folder = os.path.abspath(folder)
	print(folder, "in", input_glob, "out", output, "range", range_, "-c =",chapters, ) #"cc", chunk_ch, "cm", chunk_mb)

	# if input_glob:
	if len(input_glob) == 0:
		input_glob = [ f"*{ext}" for ext in ARCHIVE_EXTENSIONS ]
	if isinstance(input_glob, str):
		input_glob = [ input_glob ]
	for pattern in input_glob:
		if pattern.startswith("="):
			pattern = pattern[1:]
		for file_path in glob.glob(pattern, root_dir=folder):
			if Path(file_path).suffix.lower() in ARCHIVE_EXTENSIONS:
				comics_to_merge.append(file_path)
	comics_to_merge = natsorted(comics_to_merge)
	# else:
	# 	comics_to_merge = comics_in_folder(workdir=folder)

	if range_ is not None: # fallback to range
		start_idx = max(range_[0]-1, 0)
		end_idx = min(len(comics_to_merge), range_[1])
		if end_idx == -1:
			end_idx = len(comics_to_merge)
		comics_to_merge = comics_to_merge[start_idx:end_idx]

	if (len(comics_to_merge) == 0):
		print("Found no supported files for merging.")
		quit()

	if chunk_ch:
		for i in range(0, len(comics_to_merge), chunk_ch):
			chunk = comics_to_merge[i:i+chunk_ch]
			cm_instance = ComicMerge(
				f"{Path(output).stem if "." in output else output}-{i+1}-{i+chunk_ch}.cbz",
				chunk,
				first_chapter=i+1,
				chapters=chapters,
				is_verbose=not quieter,
				workdir=folder
			)
			cm_instance.merge()
	elif chunk_mb:
		cm_instance = ComicMerge(
			output, 
			comics_to_merge,
			# first_chapter=range_[0] if range_ is not None else 1, 
			chunk_mb=chunk_mb,
			chapters=chapters, 
			is_verbose=not quieter, 
			workdir=folder
		)
		cm_instance.size_chunked_merge()
	else:
		cm_instance = ComicMerge(
			output, 
			comics_to_merge,
			# first_chapter=range_[0] if range_ is not None else 1, 
			chapters=chapters, 
			is_verbose=not quieter, 
			workdir=folder
		)
		cm_instance.merge()

cli()
