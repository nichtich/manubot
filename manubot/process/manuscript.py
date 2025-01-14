import collections
import datetime
import json
import logging
import pathlib
import re

from manubot.cite.util import (
    citation_pattern,
    is_valid_citation,
)


def get_citation_ids(text):
    """
    Extract the deduplicated list of citations in a text. Citations that are
    clearly invalid such as `doi:/453` are not returned.
    """
    citation_ids = set(citation_pattern.findall(text))
    citation_ids = filter(
        lambda x: is_valid_citation(x, allow_tag=True, allow_raw=True, allow_pandoc_xnos=True),
        citation_ids,
    )
    return sorted(citation_ids)


def get_text(directory):
    """
    Return a concatenated string of section texts from the specified directory.
    """
    section_dir = pathlib.Path(directory)
    paths = sorted(section_dir.glob('[0-9]*.md'))
    name_to_text = collections.OrderedDict()
    for path in paths:
        name_to_text[path.stem] = path.read_text()
    logging.info('Manuscript content parts:\n' + '\n'.join(name_to_text))
    return '\n\n'.join(name_to_text.values()) + '\n'


def update_manuscript_citations(text, old_to_new):
    """
    Convert citations to their IDs for pandoc.

    `text` is markdown source text

    `old_to_new` is a dictionary like:
    doi:10.7287/peerj.preprints.3100v1 → 11cb5HXoY
    """
    for old, new in old_to_new.items():
        text = re.sub(
            pattern=re.escape('@' + old) + r'(?![\w:.#$%&\-+?<>~/]*[a-zA-Z0-9/])',
            repl='@' + new,
            string=text,
        )
    return text


def get_manuscript_stats(text, citation_df):
    """
    Compute manuscript statistics.
    """
    stats = collections.OrderedDict()

    # Number of distinct references by type
    ref_counts = (
        citation_df
        .standard_id
        .drop_duplicates()
        .map(lambda x: x.split(':')[0])
        .pipe(collections.Counter)
    )
    ref_counts['total'] = sum(ref_counts.values())
    stats['reference_counts'] = ref_counts
    stats['word_count'] = len(text.split())
    logging.info(f"Generated manscript stats:\n{json.dumps(stats, indent=2)}")
    return stats


def datetime_now():
    """
    Return the current datetime, with timezone awareness
    https://stackoverflow.com/a/39079819/4651668
    """
    tzinfo = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    return datetime.datetime.now(tzinfo)
