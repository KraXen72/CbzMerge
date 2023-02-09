# CbzMerge
> simple cli to merge multiple .cbz files into one

## usage
```
usage: ComicMerge [-h] [-f FOLDER] [-v] [-p PREFIX] [-r start end] [-c] OUTPUT_FILE

Merge multiple cbz files into one.

positional arguments:
  OUTPUT_FILE           Name of the .cbz file to be created. Will automatically append .cbz if necessary.

options:
  -h, --help            show this help message and exit
  -f FOLDER, --folder FOLDER
                        Input folder for comics. If blank, uses current working directory of script.
  -v, --verbose         More information as to the merging progress
  -p PREFIX, --prefix PREFIX
                        Prefix to restrict comics to
  -r start end, --range start end
                        Specified by the format X Y. Only the Xth to Yth comic in the folder will be merged into the output file.
  -c, --chapters        Don't flatten the directory tree, keep subfolders as chapters
```
## credits
- Based on [ComicMerge](https://github.com/khutchins/ComicMerge) by khutchins
  - i did some pretty major modifications to support featuers below, but full credit to khutchins for the original code
  - as per the ComicMerge's licence, ComicMerge or it's creator (khutchins) do not endorse or are associated with CbzMerge

## feaures added in CbzMerge
- works without providing either range or prefix (merges all comics in folder)
- `-c`/`--chapters` flag, outputs a cbz with internally separated chapters by folders
- `-f`/`--folder` flag, provide path to your comics that will be read & processed. comics there are not touched.
- proper information about merging progress in stdout
- under the hood rewrites
  
### notes:
- This script will probably work on Linux, Mac, and Windows, but it has only been tested on Windows.
- The `-f`/`--folders` flag was tested on PocketBook Touch Lux 4, it does create chapters internally in it's reader.

## license
This project is licensed under the BSD license. For more information, check out LICENSE.md.
