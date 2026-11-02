"""The seed SQL must be a build artefact of data/, not a second source of truth.

Adding a skill to taxonomy.yaml and forgetting docs/sql/002_seed.sql produces a
database that looks broken (31 rows where the vocabulary says 32). This test makes
that mistake a red build instead of a mystery.
"""
import importlib.util
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "gen_seed.py"
SEED = REPO / "docs" / "sql" / "002_seed.sql"


def load_generator():
    spec = importlib.util.spec_from_file_location("gen_seed", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_seed_sql_matches_the_data_files():
    generated = load_generator().build()
    assert SEED.exists(), "docs/sql/002_seed.sql is missing"
    assert SEED.read_text(encoding="utf-8").strip() == generated.strip(), (
        "docs/sql/002_seed.sql is out of date with data/taxonomy.yaml or data/curated.yaml — "
        "run: python scripts/gen_seed.py"
    )


def test_generated_seed_counts_its_own_rows():
    import yaml

    taxonomy = yaml.safe_load((REPO / "data" / "taxonomy.yaml").read_text(encoding="utf-8"))
    generated = load_generator().build()
    for skill in taxonomy["skills"]:
        assert f"('{skill['id']}', '{skill['name']}'" in generated
        for subtopic in skill["subtopics"]:
            assert f"'{subtopic['id']}'" in generated


def test_generator_refuses_a_skill_with_no_subtopics(tmp_path):
    """A skill with no curriculum cannot produce a roadmap, so it is a build error."""
    import yaml

    module = load_generator()
    taxonomy = {"skills": [{"id": "x", "name": "X", "category": "AI", "aliases": [],
                            "interview_relevance": 0.5, "subtopics": []}]}
    path = tmp_path / "taxonomy.yaml"
    path.write_text(yaml.safe_dump(taxonomy), encoding="utf-8")
    module.TAXONOMY = path
    try:
        module.build()
    except SystemExit as exc:
        assert "subtopics" in str(exc)
    else:
        raise AssertionError("expected SystemExit for a skill with no subtopics")


def test_every_curated_url_is_used_once():
    """resources.url is unique; the generator must refuse a catalogue that repeats one."""
    import yaml

    catalogue = yaml.safe_load((REPO / "data" / "curated.yaml").read_text(encoding="utf-8"))
    urls = [
        entry["url"]
        for by_sub in catalogue["catalogue"].values()
        for entries in by_sub.values()
        for entry in entries
    ]
    assert len(urls) == len(set(urls)), "curated.yaml repeats a URL"


def test_generator_refuses_a_dangling_subtopic(tmp_path):
    """A curated entry pointing at a subtopic taxonomy.yaml lacks would fail the FK on paste."""
    import yaml

    module = load_generator()
    taxonomy = {"skills": [{"id": "x", "name": "X", "category": "AI", "aliases": [],
                            "interview_relevance": 0.5,
                            "subtopics": [{"id": "real", "title": "Real", "level": "beginner",
                                           "objective": "o"}]}]}
    curated = {"catalogue": {"x": {"invented": [
        {"url": "https://example.org/a", "title": "A", "kind": "article", "verified": False}]}}}
    tax_path = tmp_path / "taxonomy.yaml"
    cur_path = tmp_path / "curated.yaml"
    tax_path.write_text(yaml.safe_dump(taxonomy), encoding="utf-8")
    cur_path.write_text(yaml.safe_dump(curated), encoding="utf-8")
    module.TAXONOMY, module.CURATED = tax_path, cur_path
    try:
        module.build()
    except SystemExit as exc:
        assert "x/invented" in str(exc)
    else:
        raise AssertionError("expected SystemExit for a dangling subtopic")


def test_content_and_growth_topics_can_now_be_taught():
    """Phase 5's honesty gate: the content/growth half of the vocabulary used to have
    zero resources, so every roadmap topic reported all three roles missing."""
    import yaml

    taxonomy = yaml.safe_load((REPO / "data" / "taxonomy.yaml").read_text(encoding="utf-8"))
    catalogue = yaml.safe_load((REPO / "data" / "curated.yaml").read_text(encoding="utf-8"))[
        "catalogue"
    ]
    covered = {sid for sid in catalogue if sid.startswith(
        ("content-strategy", "social-growth", "newsletter", "seo", "marketing-analytics",
         "experimentation", "short-form-video", "visual-design", "copywriting", "ai-workflows"))}
    kinds = {k["id"]: k for k in taxonomy["skills"]}
    assert covered.issubset(kinds), "curated.yaml names a content skill that does not exist"
    # And every one of those skills must actually teach at least one subtopic.
    for skill_id in covered:
        assert catalogue[skill_id], f"{skill_id} has an empty curated block"
