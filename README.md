# cbzmerge v2
merge them comic books (& more)

## installation
use with python 3.11+ (3.8 should work too, but not tested)
```shell
git clone https://github.com/KraXen72/CbzMerge
cd CbzMerge
pip install -r requirements.txt
```

## usage
```shell
python -m cmerge -f "D:\#stuff\#komga\hakuneko\Tokyo Ghoul" -i='*.cbz' --range 1 3 tg1-3.cbz
```
- `--in`, `-i` - Input globs relative to the `--folder`.
  - due to windows powershell auto-expanding globs with a star, pass it with a `=`, e.g. `-i='*.cbz'`
  - you can add multiple glob patterns: `-i='*.cbz' -i='*.cbr'`
- `--folder`, `-f` - Path to the input folder
- `--range`, `-r` - Range of chapters in folder (sorted alphabetically, ascending) which will be processed. e.g. `-r 1 3`
  - inclusive start & end, the first file is 1, not 0. will be clamped. you can use -1 as start/end (`-r 22:-1`)
- `--chapters`, `-c` - Don't flatten the directory tree, keep subfolders as chapters
- see `python -m cmerge --help` for all options

## notes 
- if any of the chapters has a `ComicInfo.xml`, it will be taken into account

## notice & credits
CbzMerge was initially based on [ComicMerge](https://github.com/khutchins/ComicMerge) by Kevin Hutchins.  
CbzMerge is not, in any way, endorsed by or affiliated with ComicMerge.  
You can find ComicMerge's license in the `LICENSE-ComicMerge.md` file.  
The rest of the project is licensed in MIT. Make sure to respect the original license as well.
  
Copyright (c) 2014, Kevin Hutchins All rights reserved.  
Copyright (c) 2024 KraXen72  