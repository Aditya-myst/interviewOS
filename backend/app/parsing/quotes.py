"""The quote gate — the reason this product can be trusted.

Every skill claim, in either direction, carries a `quote`. This module answers one
question about a quote: *does it actually appear in the document?* — and if so,
where. Whitespace differences (a PDF that broke a line mid-phrase) are tolerated;
invented, paraphrased or edited text is not.

This is deliberately the only path from "a model said so" to "a row in the
database". Callers that skip it can produce a believable profile of a person who
does not exist.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

MAX_QUOTE_CHARS = 300
MIN_QUOTE_CHARS = 8


@dataclass
class VerifiedQuote:
    quote: str
    start: int
    end: int

    def as_evidence(self, kind: str, **extra) -> dict:
        return {"type": kind, "quote": self.quote, "start": self.start, "end": self.end, **extra}


def _flexible_pattern(quote: str) -> str:
    """Every run of whitespace in the quote may be any run of whitespace in the doc."""
    words = [re.escape(w) for w in quote.split()]
    return r"\s+".join(words)


def verify(quote: str, text: str) -> VerifiedQuote | None:
    """Return the located span, or None if this quote is not in the document.

    None is not an error — it is the gate closing. The caller drops the claim and
    records why.
    """
    candidate = " ".join(quote.split()).strip()
    if len(candidate) < MIN_QUOTE_CHARS:
        return None
    if len(candidate) > MAX_QUOTE_CHARS:
        candidate = candidate[:MAX_QUOTE_CHARS].rsplit(" ", 1)[0]

    match = re.search(_flexible_pattern(candidate), text, flags=re.IGNORECASE)
    if match is None:
        return None
    return VerifiedQuote(quote=text[match.start() : match.end()], start=match.start(), end=match.end())


def verify_all(quotes: list[str], text: str) -> tuple[list[VerifiedQuote], list[str]]:
    """Split quotes into (kept, rejected). Rejections are logged, never silently dropped."""
    kept: list[VerifiedQuote] = []
    rejected: list[str] = []
    for quote in quotes:
        found = verify(quote, text)
        if found is None:
            rejected.append(quote)
        else:
            kept.append(found)
    return kept, rejected


SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+|\n+|(?<=[;•·])\s+|\s{3,}")


def sentence_around(text: str, start: int, end: int, *, max_chars: int = 240) -> tuple[str, int, int]:
    """Grow a mention out to the sentence that contains it, without crossing lines.

    Quoting a whole paragraph makes evidence unreadable in the UI; quoting two
    words makes it unfalsifiable. One sentence is the unit that a recruiter can
    check by eye in five seconds.
    """
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    if len(line) > max_chars * 2:  # a wall of text: fall back to the sentence
        line = text[max(0, start - max_chars) : min(len(text), end + max_chars)]
        line_start = max(0, start - max_chars)

    offset = start - line_start
    bounds: list[tuple[int, int]] = []
    cursor = 0
    for piece in SENTENCE_BREAK.split(line):
        if not piece:
            continue
        index = line.find(piece, cursor)
        if index == -1:
            continue
        bounds.append((index, index + len(piece)))
        cursor = index + len(piece)

    for lo, hi in bounds:
        if lo <= offset < hi:
            chosen = (lo, hi)
            break
    else:
        chosen = (0, len(line))

    quote = line[chosen[0] : chosen[1]].strip(" •-–—\t")
    if len(quote) > max_chars:
        quote = quote[:max_chars].rsplit(" ", 1)[0]
    # strip leading whitespace so offsets stay honest
    lead = len(line[chosen[0] : chosen[1]]) - len(line[chosen[0] : chosen[1]].lstrip(" •-–—\t"))
    absolute_start = line_start + chosen[0] + lead
    return quote, absolute_start, absolute_start + len(quote)
