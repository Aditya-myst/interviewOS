"""Words that address the candidate rather than name a concept.

Both scorers build rubrics out of curriculum prose, and curriculum prose is written as
instructions: "Explain generation limits without mysticism", "Measure recall@k and improve
retrieval quality". Left in a rubric, those words become demands, an answer that says
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
        # connectives: they hold a sentence together, they are not a concept. "Scope before
        # designing" used to make **before** a rubric point, so an answer about scope scored
        # as if it had missed something.
        "before", "after", "during", "while", "between", "across", "through", "over", "under",
        "against", "onto", "within", "into", "each", "every", "both", "either", "neither",
        "much", "many", "more", "most", "less", "least", "rather", "back", "down", "off",
        "again", "still", "yet", "now",
    }
)

# The same idea wearing a different word. The deterministic scorer has no model to ask
# "do these mean the same thing", so the dictionary is explicit and small: one entry per
# curriculum concept that candidates reliably phrase another way. Keys are rubric terms
# (lower case); values are alternates that count as the same point. Anything not listed
# still has to be said in the rubric's own vocabulary, this widens the door, it does not
# open it: the answer must still be specific, quotable and sentence-length to score.
CONCEPT_SYNONYMS: dict[str, tuple[str, ...]] = {
    # system design
    "envelope": ("budget", "estimate", "calculate"),
    "maths": ("math", "arithmetic", "numbers", "calculation"),
    "scope": ("bound", "boundary", "constraint", "limit"),
    "primitive": ("building", "component", "block"),
    "balancing": ("balancer", "balance"),
    "queues": ("queue", "backlog", "buffer"),
    "replication": ("replica", "replicas", "copy"),
    "consistency": ("consistent", "consensus", "invariant"),
    "observability": ("monitoring", "metrics", "telemetry", "traces"),
    "failure": ("failover", "fallback", "degrade", "circuit", "resilience"),
    # retrieval and models
    "recall": ("retrieved", "retrieval", "hits"),
    "rerank": ("reranking", "reranker", "reranked"),
    "embeddings": ("embedding", "vector", "vectors"),
    "chunking": ("chunk", "chunks", "chunked"),
    "tokens": ("token", "tokenise", "tokenize", "tokenisation"),
    "faithfulness": ("grounded", "hallucination", "hallucinations", "citation"),
    "leakage": ("leak", "leaking", "contaminated"),
    "overfitting": ("overfit", "generalise", "generalize"),
    "imbalance": ("imbalanced", "skewed", "rare"),
    "variance": ("spread", "volatility"),
    "caching": ("cache", "cached"),
    "indexing": ("index", "indexes", "indices"),
    "concurrency": ("concurrent", "parallel", "asynchronous", "async"),
    "latency": ("p99", "p95", "delay", "slow"),
}

__all__ = ["CONCEPT_SYNONYMS", "INSTRUCTION_WORDS"]
