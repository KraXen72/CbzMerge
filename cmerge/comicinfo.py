import xml.etree.ElementTree as ElementTree
from typing import NotRequired, TypedDict


class ComicInfo(TypedDict):
	Title: NotRequired[str]
	Series: NotRequired[str]
	Number: NotRequired[str]
	Count: NotRequired[int]
	Volume: NotRequired[int]
	AlternateSeries: NotRequired[str]
	AlternateNumber: NotRequired[str]
	AlternateCount: NotRequired[int]
	Summary: NotRequired[str]
	Notes: NotRequired[str]
	Year: NotRequired[int]
	Month: NotRequired[int]
	Writer: NotRequired[str]
	Penciller: NotRequired[str]
	Inker: NotRequired[str]
	Colorist: NotRequired[str]
	Letterer: NotRequired[str]
	CoverArtist: NotRequired[str]
	Editor: NotRequired[str]
	Publisher: NotRequired[str]
	Imprint: NotRequired[str]
	Genre: NotRequired[str]
	Web: NotRequired[str]
	PageCount: NotRequired[int]
	LanguageISO: NotRequired[str]
	Format: NotRequired[str]
	BlackAndWhite: NotRequired[str]
	Manga: NotRequired[str]

def parse_comicinfo(fp: str) -> ComicInfo: 
	tree = ElementTree.parse(fp)
	root = tree.getroot()

	comic_info: ComicInfo = {}
	for child in root:
		comic_info[child.tag] = child.text
	return comic_info


