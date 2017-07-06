import argparse
import sys
from ComicMerge import ComicMerge

parser = argparse.ArgumentParser(prog='ComicMerge', description='Merge multiple cbz files into one.')
parser.add_argument('-v', '--verbose', action='store_true', help='More information as to the merging progress')
parser.add_argument('output_name', metavar='OUTPUT_FILE', type=str,
                    help='Name of the .cbz file to be created. Will automatically append .cbz if necessary.')
parser.add_argument('-r', '--range', nargs=2, metavar=('start', 'end'), type=int,
                    help='Specified by the format X Y. Only the Xth to Yth comic in the folder will be merged into the '
                         'output file.')
args = parser.parse_args()

comics_to_merge = []
if (len(args.range)) == 0:
    comics_to_merge.extend(ComicMerge.comics_from_indices(0, -1))
else:
    comics_to_merge.extend(ComicMerge.comics_from_indices(args.range[0], args.range[1]))
comic_merge = ComicMerge(args.output_name, comics_to_merge, args.verbose)
comic_merge.merge()
