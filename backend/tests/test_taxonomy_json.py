"""contracts/taxonomy.json is a build artefact, not a second source of truth.

The landing page prints "41 skills / 137 subtopics / 75 links" from that file. If it
drifts from data/, the marketing page starts advertising a catalogue the product does
not have — the exact failure this project is built to avoid.
"""
import importlib.util
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "gen_taxonomy_json.py"
PUBLISHED = REPO / "contracts" / "taxonomy.json"


def load_generator():
    spec = importlib.util.spec_from_file_location("gen_taxonomy_json", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_published_json_matches_the_data_files():
    assert PUBLISHED.exists(), "contracts/taxonomy.json is missing — run scripts/gen_taxonomy_json.py"
    published = json.loads(PUBLISHED.read_text(encoding="utf-8"))
    generated = load_generator().build()
    # _comment is identical too, so a full compare is fair.
    assert published == generated, "contracts/taxonomy.json is out of date with data/"


def test_totals_count_what_the_files_contain():
    import yaml

    taxonomy = yaml.safe_load((REPO / "data" / "taxonomy.yaml").read_text(encoding="utf-8"))
    curated = yaml.safe_load((REPO / "data" / "curated.yaml").read_text(encoding="utf-8"))
    totals = json.loads(PUBLISHED.read_text(encoding="utf-8"))["totals"]

    assert totals["skills"] == len(taxonomy["skills"])
    assert totals["subtopics"] == sum(len(s["subtopics"]) for s in taxonomy["skills"])
    assert totals["resources"] == sum(
        len(rows) for by_sub in curated["catalogue"].values() for rows in by_sub.values()
    )
