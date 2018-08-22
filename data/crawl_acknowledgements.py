#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Crawl article's html files for acknowledgments and
output one file per journal-year.
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup

SOURCE_FILE = "./DOIs.csv"
TARGET_FOLDER = "./crawler_output/"

# Years of journals for which we can crawl information
KEEP = {"JF": range(2004, 2011+1), "JMCB": range(2007, 2011+1),
        "RFS": range(2004, 2011+1),"JFI": range(1997, 2011+1),
        "JFE": range(1997, 2011+1), "JBF": range(1997, 2011+1)}
# Strings indicating meta articles
_metakeywords = ["MISCELLANEA", "MINUTES OF THE ANNUAL", "REPORT OF THE EDITOR",
                 "REPORT OF THE EXECUTIVE SECRETARY AND TREASURER", "FOREWORD",
                 "A NOTE FROM THE EDITOR", "DISCUSSION OF", "EDITORS’ NOTE",
                 "EDITORS' NOTE", "EDITORS’ INTRODUCTION",
                 "EDITORS' INTRODUCTION", "EDITOR'S INTRODUCTION",
                 "CORRIGENDUM", "ERRATUM", "FRONT MATTER", "BACK MATTER"]

def abbreviate(journal):
    """Abbreviate journal name."""
    j = journal.replace(" OF ", " ").replace(" AND ", " ").replace("& ", "")
    return "".join(n[0] for n in j.split())


def append_thanks_to_output(thanklist, tag):
    """Append cleaned acknowledgment section."""
    thanks = clean_string(tag)
    if not thanks == "":
        return thanklist.append("THANKS: {}\n".format(thanks))


def contains_carriage_return(text):
    """Check if carriage return is present."""
    return "↵" in clean_string(text)


def is_keyword(text):
    """Check whether text is likely to be a keyword."""
    return len(text.strip()) < 4 and text.isalpha()


def is_meta_article(title):
    """Check if a given title does indicate a non-research article."""
    return any(keyword in title for keyword in _metakeywords)


def clean_string(dirt):
    """Remove clutter from a string."""
    dirt = "".join(i if ord(i) < 128 else ' ' for i in dirt)
    try:
        dirt = dirt.encode("utf8").upper()
    except UnicodeDecodeError:
        dirt = dirt.upper()
    if dirt.endswith('AND'):
        dirt = dirt.split(' AND', 1)[0]
    if dirt.endswith('CORRESPONDING AUTHOR.'):
        dirt = dirt.split(' CORRESPONDING AUTHOR.', 1)[0]
    clean = (dirt.strip().strip('*').strip('☆').strip(',').strip().strip('*')
                 .lstrip('1234567890').rstrip('1234567890-,'))
    clean = " ".join(clean.split())
    return (clean.replace("ACKNOWLEDGMENTS", "")
                 .replace("ACKNOWLEDGEMENTS", "")
                 .replace("PREVIOUS SECTIONNEXT SECTION", "")
                 .strip().rstrip(',')))


def get_clean_affs(tags, lookup):
    """Return list of standarized affiliations."""
    repl = [clean_string(tag) for tag in tags]
    subs = sorted(list(set([item for sl in lookup for item in sl])))
    lookup_dict = dict(zip(subs, repl))
    for sub in lookup_dict:  # replace
        aff_list = [[aff.replace(sub, lookup_dict[sub]) for aff in l]
                    for l in aff_list]


def process(df):
    """Parse all DOIs of DataFrame."""
    dois = df["DOI"]
    journal = df["Journal"]
    year = df["Year"]
    output = []
    for doi in dois:
        html = requests.get("http://dx.doi.org/" + doi)
        soup = BeautifulSoup(html, 'lxml')
        output.append(parse(soup))
    return output


def parse(soup, journal):
    """Parse a single file depening on the journal."""
    auth_list, aff_list = [], []
    if journal == "JFI":  # check if article is a Regular Article
        publication_type = soup.find('div', {'class': 'publicationType'})
        if publication_type is not None and publication_type.text != "Regular Article":
            return None
    # TITLE
    try:
        title_tag = soup.find()
        if journal == "RFS":
            title = soup.find("h1", {"id": "article-title-1"}).text
        elif journal in ("JFI", "JFE", "JBF"):
            title = soup.find("li", {"class": 'originalArticleName'}).text
        else:
            title = soup.find("span", {"class": "mainTitle"}).text
    except AttributeError:
        print("No title found")
        pass
    title = title.replace("\n", "").upper().encode('utf-8')
    title = " ".join(title.split())
    if is_meta_article(title):
        return None
    output.append("TITLE: {}\n".format(title))
    # AUTH
    if journal == "RFS":
        for author in soup.find_all('a', {"class": "name-search"}):
            auth_list.append("AUTH: {}\n".format(clean_string(author.text)))
    if journal in ("JFI", "JFE", "JBF"):  # two possibilities
        subscripts_list = []
        for author in soup.find_all('a', {"class": "authorName svAuthor"}):
            auth_list.append("AUTH: {}\n".format(clean_string(author.text)))
        auth_entries = soup.find_all(
            'a', {"class": "authorName S_C_authorName svAuthor"})
        for author in auth_entries:
            auth_list.append("AUTH: {}\n".format(clean_string(author.text)))
            nextSubscript = author
            while True:  # Get affiliation subscripts
                nextSubscript = nextSubscript.nextSibling
                try:
                    if nextSubscript.text.isalpha():
                        subscripts_list.append(nextSubscript.text)
                except AttributeError:
                    break
            if subscripts_list != []:
                aff_list.append(subscripts_list)
            subscripts_list = []
    else:
        for authortag in soup.find_all('ol', {"id": "authors"}):
            for author in authortag.findChildren('li'):
                auth_list.append("AUTH: {}\n".format(clean_string(author.text)))
    # AFF
    if journal == "RFS":
        for affiliation in soup.find_all('li', {"class": "aff"}):
            aff_list.append("AFF: {}\n".format(clean_string(affiliation.text)))
    elif journal in ("JFI", "JFE", "JBF"):  # create dictionary for subscripts
        afftags = soup.find_all(
            lambda e: getattr(e, 'name', None) == 'span' and
            e.attrs.get('id') == '')
        try:
            if afftags[0].text == "Regular Article":
                # remove possible first item
                del afftags[0]
        except IndexError:  # sometimes there are no affiliations
            aff_list.append(["check online"])
        if aff_list == []:  # one affiliation (for possibly many authors)
            aff_list = ["AFF: {}\n".format(clean_string(afftags[0].text))]
        else:  # multiple affiliations
            affs = get_clean_affs(afftag.text, aff_list)
            aff_list = ["AFF: {}\n".format("; ".join(list)) for list in affs]
    else:
        for afftag in soup.find_all('ol', {"id": "authorsAffiliations"}):
            for aff in afftag.findChildren('li'):
                aff_list.append("AFF: {}\n".format(clean_string(aff.text)))
    # Sort AUTH and AFF alternatively
    if aff_list in ([], [[]]):
        output.append(''.join(map(str, auth_list)))
    else:  # make sure there are enough affiliations
        if len(aff_list) < len(auth_list):
            if len(set(aff_list)) == 1:  # one affiliation for all authors
                aff = [aff_list[0]]
                aff_list.extend(aff*(len(auth_list) - len(aff_list)))
            else:
                aff_list = ["AFF: check online\n"]*len(auth_list)
        auth_aff_list = zip(auth_list, aff_list)
        auth_aff_list = [item for sublist in auth_aff_list for item in sublist]
        output.append(''.join(map(str, auth_aff_list)))
    # THANKS
    if journal == "JMCB":  # one possibility
        for thanktag in soup.find_all("ol", {"id": "footnotes"}):
            append_thanks_to_output(output, thanktag.text)
    elif journal == "RFS":  # five possibilities
        # from http://codereview.stackexchange.com/a/87028/59669
        thanktag_queries = [
            ("div", {"class": "section ack"}, 0),
            ("li", {"class": "fn-con"}, 0),
            ("li", {"class": "fn fn-group-arthw-misc"}, 0),
            ("li", {"id": "fn-1"}, 0)
        ]
        thanktag = None
        for i in xrange(len(thanktag_queries)):
            thanktag_query = thanktag_queries[i]
            soup_result = soup.find_all(thanktag_query[0], thanktag_query[1])
            if len(soup_result) > thanktag_query[2]:
                thanktag = soup_result[0]
                if i == len(thanktag_queries):
                    if not contains_carriage_return(unicode(thanktag.text)):
                        thanktag = soup_result[-2]
                break
        if not (thanktag is None and contains_carriage_return(thanktag.text)):
            thanks = clean_string(thanktag.text)
            append_thanks_to_output(output, thanks)
    elif journal == "JF":  # two possibilities
        for thanktag in soup.find_all('p', {"id": "correspondence"}):
            thanks = thanktag
        if 'thanktag' not in globals():
            for thanktag in soup.find_all('ul', {"id": "footnotes"}):
                thanks = thanktag
        else:
            append_thanks_to_output(output, thanks.text)
    elif journal in ("JFI", "JFE", "JBF"):  # three possibilities
        try:
            thanktag = soup.find('div', {'class': 'articleText_indent'})
            append_thanks_to_output(output, thanktag.text)
        except AttributeError:
            for thanktag in soup.find_all('dl', {'id': 'item1'}):
                append_thanks_to_output(output, thanktag.text)
        if thanktag is None:
            thanktag = soup.find('div', {'class': 'artFooterContent'}).text
            if len(thanktag) < 1000:
                append_thanks_to_output(output, thanktag)
    # JEL
    jel_list = []
    if journal == "RFS":
        for jeltag in soup.find_all('li', {"class": "kwd"}):
            jel_list.append(jeltag.text)
    if journal in ("JF", "JMCB"):
        for jeltag in soup.find_all('meta', {"name": "citation_keywords"}):
            if not is_keyword(jeltag['content']):
                jel_list.append(jeltag['content'])
    else:  # two possibilities
        for jeltag in soup.find_all('li', {'class': 'svKeywords'}):
            jeltag = jeltag.text.strip('; ')
            if not is_keyword(jeltag):
                jel_list.append(jeltag)
        if jel_list == []:
            abstract = soup.find('div', {"class": 'abstract svAbstract '})
            if abstract is not None:
                jel_codes = abstract.text.split(':')[-1]
                if len(jel_codes) < 50:
                    jel_list = jel_codes.strip().rstrip(".").split(', ')
    if jel_list != []:
        output.append("JEL: {}\n".format('; '.join(jel_list)))
    # End of entry
    output.append("\n")
    return output


def read_doilist():
    """Return processed DOI list file."""
    df = pd.read_csv(SOURCE_FILE, usecols=["Journal", "Year", "DOI"])
    journals = set(df["Journal"])
    mapping = {j: abbreviate(j) for j in journals}
    df["Journal"] = df["Journal"].replace(mapping)
    return df.sort_values("Year")


def main():
    df = read_doilist()
    
    combs = []
    for j in KEEP:
        combs.extend([(j, y) for y in KEEP[j]])

    for journal, year in combs:
        subset = df[(df["Journal"] == journal) & (df["Year"] == year)]
        output = process(subset.iloc[1:2])
        ouf = "TARGET_FILE{}-{}.dat".format(journal, year)
        with open(ouf, 'a') as ouf:
            ouf.write(str(''.join(map(str, output))))


if __name__ == '__main__':
    main()
