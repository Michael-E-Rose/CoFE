Folder contains sorted acknowledgements in [`raw_acks`](raw_acks).  They were generated manually, partly using the crawler output in folder [`crawler_output`](crawler_output), which was obtained through [`crawl_acknowledgements.py`](crawl_acknowledgements.py).

** Filelist **
* [`DOIs.csv`](DOIs.csv) contains titles and DOIs for all the articles that we use to construct the network of informal intellectual collaboration from.
* [`crawl_acknowledgements.py`](crawl_acknowledgements.py) crawls acknowledgements from web version of an article using its DOI.
* [`persons.csv`](persons.csv) maps each entry in a person category to its alias, which is usually the ID to the researcher's Scopus profile.
* [`institutions.csv`](institutions.csv) maps each entry in an institution category to its alias.

We exclude notes, dicussions, replies, shorter papers (a JMCB section), book reviews, editorials, announcements, etc.
