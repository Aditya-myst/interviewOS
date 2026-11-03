"""Words that address the candidate rather than name a concept.

Both scorers build rubrics out of curriculum prose, and curriculum prose is written as
instructions: "Explain generation limits without mysticism", "Measure recall@k and improve
retrieval quality". Left in a rubric, those words become demands — an answer that says
everything about token limits but never says the word "mysticism" is scored as incomplete.

Keeping one list means the interview and the assessment cannot disagree about what counts
as a concept.
"""
from __future__ import annotations

INSTRUCTION_WORDS = frozenset(
    {
        # adverbs and qualifiers
        "correctly", "properly", "cleanly", "quickly", "without", "really", "actually",
        "enough", "given", "following", "also", "only", "ever", "never", "always",
        # what to do with knowledge, not the knowledge
        "explain", "explains", "describe", "describes", "identify", "state", "list", "know",
        "understand", "use", "uses", "using", "make", "makes", "take", "takes", "give",
        "gives", "get", "gets", "run", "runs", "write", "writes", "read", "reads", "build",
        "builds", "design", "designs", "test", "tests", "choose", "chooses", "pick", "picks",
        "keep", "keeps", "apply", "applies", "ensure", "avoid", "handle", "handles",
        "manage", "manages", "measure", "measures", "improve", "improves", "plan", "plans",
        "compare", "evaluate", "decide", "turn", "turns", "work", "works", "go", "goes",
        "put", "set", "sets", "show", "shows", "walk", "cover", "covers",
        # empty nouns
        "fundamentals", "basics", "concepts", "basic", "simple", "common", "typical",
        "correct", "right", "better", "proper", "clear", "thing", "things", "way", "ways",
        "part", "parts", "point", "points", "level", "levels", "kind", "kinds", "sort",
        "job", "jobs", "problem", "problems", "case", "cases", "example", "examples",
        "first", "next", "last", "small", "large", "good", "bad", "new", "old", "own",
        "actual", "real", "same", "different", "others", "someone", "something", "else",
        "must", "should", "able", "need", "needs", "want", "wants", "start", "starts",
    }
)

__all__ = ["INSTRUCTION_WORDS"]
