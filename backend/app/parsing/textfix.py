"""Repair text that was decoded with the wrong codec on the way in.

Where "â€œunderstanding why content worksâ€" comes from: UTF-8 bytes decoded as
cp1252/latin-1 — usually by a PDF extractor or a Windows tool that assumes a legacy
codepage. It is not merely ugly. It breaks the product's central promise, because a quote
shown in a report has to be the candidate's *actual* words: a mangled quote is
verbatim-but-wrong.

Two passes, most faithful first:

1. round trip the whole string through cp1252/latin-1 and re-decode as UTF-8 — perfect
   when the corruption is intact;
2. otherwise substitute the known fragments. The second pass exists because truncation
   happens: a console, a column limit or a paste can cut "â€œ" down to "â€", and a strict
   round trip then refuses the entire document. Fixing ninety percent of a document beats
   refusing all of it.

The repair is timid on purpose: it only fires when the text carries fingerprints of the
bug, and text that is simply French is left alone.
"""
from __future__ import annotations

import re

# Sequences that essentially never occur in real prose but appear immediately when UTF-8
# has been read as cp1252: the trademark of the bug.
FINGERPRINTS = (
    "â€",  # curly quotes, dashes, ellipsis
    "Â«",
    "Â»",
    "Â ",
    "Ã ",  # A-grave split by a space
    "Ã©",
    "Ã¨",
    "Ã¢",
    "Ã´",
    "Ã®",
    "Ã§",
    "Ã¼",
    "Ã¶",
    "Ã¤",
    "ï»¿",  # BOM that arrived as text
)

# Fragment -> what it should have been. Longest first: "â€œ" must win over "â€".
FRAGMENTS = {
    "â€œ": "\u201c",
    "â€\x9d": "\u201d",
    "â€™": "\u2019",
    "â€˜": "\u2018",
    "â€“": "\u2013",
    "â€”": "\u2014",
    "â€¦": "\u2026",
    "â€¹": "\u2039",
    "â€º": "\u203a",
    "â„¢": "\u2122",
    "Â«": "\u00ab",
    "Â»": "\u00bb",
    "Â°": "\u00b0",
    "Â ": "\u00a0",
    "Ã€": "\u00c0",
    "Ã ": "\u00e0",
    "Ã©": "\u00e9",
    "Ã¨": "\u00e8",
    "Ãª": "\u00ea",
    "Ã¢": "\u00e2",
    "Ã´": "\u00f4",
    "Ã®": "\u00ee",
    "Ã§": "\u00e7",
    "Ã¹": "\u00f9",
    "Ã»": "\u00fb",
    "Ã«": "\u00eb",
    "Ã¯": "\u00ef",
    "Ã±": "\u00f1",
    "Ã¼": "\u00fc",
    "Ã¶": "\u00f6",
    "Ã¤": "\u00e4",
    "ÃŸ": "\u00df",
    "ï»¿": "",
}


# A lone "â" or "Â" standing between punctuation and nothing is the tail of a character
# that was cut in half — no language has a word made only of those letters. This is what a
# truncated "â€™" looks like once the rest has been dropped.
ORPHANS = re.compile(r"(?<![^\W\d_])[âÂ](?![^\W\d_])")


def _fingerprints(text: str) -> int:
    return sum(text.count(marker) for marker in FINGERPRINTS)


def _by_fragment(text: str) -> str:
    for fragment in sorted(FRAGMENTS, key=len, reverse=True):
        text = text.replace(fragment, FRAGMENTS[fragment])
    return text


def repair_mojibake(text: str) -> tuple[str, bool]:
    """(repaired_text, changed). Never raises, never loses text silently."""
    if not text:
        return text, False

    if _fingerprints(text) == 0:
        stripped = ORPHANS.sub("", text)
        return (stripped, True) if stripped != text else (text, False)

    before = _fingerprints(text)

    # Pass 1 — the clean case: the whole string is intact mojibake.
    for codec in ("cp1252", "latin-1"):
        try:
            candidate = text.encode(codec, errors="strict").decode("utf-8", errors="strict")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if _fingerprints(candidate) < before:
            return candidate, True

    # Pass 2 — fragments, including truncated ones.
    candidate = _by_fragment(text)
    # A leftover "â€" is a broken fragment of a character we cannot recover; drop it rather
    # than show it, and say the text was repaired so the warning travels.
    candidate = ORPHANS.sub("", candidate.replace("â€", ""))
    if _fingerprints(candidate) < before:
        return candidate, True
    return text, False
