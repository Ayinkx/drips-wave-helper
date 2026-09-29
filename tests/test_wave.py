import json

import wave

CFG = {
    "github_username": "Ayinkx",
    "display_name": "Ayinkx",
    "full_name": "Lawal Olayinka Awal",
    "roles": ["Python Developer", "Open Source Contributor"],
    "skills": ["python", "rust"],
    "labels": ["stellar-wave"],
    "slots": 15,
    "pitch": "I ship small, well-tested slices.",
    "links": {"github": "https://github.com/Ayinkx"},
    "addons": ["Happy to share a short plan."],
}


def make_issue(**overrides):
    issue = {
        "repo": "owner/repo",
        "number": 12,
        "title": "Python task",
        "body": "",
        "labels": [],
        "created_at": "2000-01-01T00:00:00Z",
        "updated_at": "2000-01-01T00:00:00Z",
    }
    issue.update(overrides)
    return issue


# --------------------------------------------------------------------------- #
# word_in
# --------------------------------------------------------------------------- #


def test_word_in_matches_whole_words_case_insensitively():
    assert wave.word_in("We need a Python developer", "python")
    assert wave.word_in("PYTHON", "python")


def test_word_in_does_not_match_substrings():
    assert not wave.word_in("micropython is fun", "python")
    assert not wave.word_in("rusty metal", "rust")


def test_word_in_handles_multi_word_and_symbol_needles():
    assert wave.word_in("build a REST API client", "REST API")
    assert wave.word_in("we use c++ here", "c++")


# --------------------------------------------------------------------------- #
# issue_key / parse_ref
# --------------------------------------------------------------------------- #


def test_issue_key():
    assert wave.issue_key({"repo": "owner/repo", "number": 7}) == "owner/repo#7"


def test_parse_ref_from_github_url():
    assert (
        wave.parse_ref("https://github.com/Ayinkx/drips-wave-helper/issues/12")
        == "Ayinkx/drips-wave-helper#12"
    )


def test_parse_ref_from_shorthand_and_whitespace():
    assert wave.parse_ref("  Ayinkx/repo#12  ") == "Ayinkx/repo#12"
    assert wave.parse_ref("Ayinkx/repo 12") == "Ayinkx/repo#12"


def test_parse_ref_falls_back_to_input():
    assert wave.parse_ref("not-a-reference") == "not-a-reference"


# --------------------------------------------------------------------------- #
# score_issue
# --------------------------------------------------------------------------- #


def test_score_issue_counts_matching_skills():
    score, matched = wave.score_issue(make_issue(), CFG)
    assert matched == ["python"]
    assert score == 10  # 10 per matched skill, no bonuses, stale by design


def test_score_issue_applies_good_first_issue_and_bug_bonuses():
    issue = make_issue(title="Fix python bug", labels=["good first issue"])
    score, matched = wave.score_issue(issue, CFG)
    assert matched == ["python"]
    assert score == 10 + 25 + 3  # skill + good first issue + bug


def test_score_issue_without_skill_matches_has_no_skill_points():
    issue = make_issue(title="Write release notes", body="documentation help")
    score, matched = wave.score_issue(issue, CFG)
    assert matched == []
    assert score == 2  # only the "documentation" bonus


def test_score_issue_is_deterministic():
    issue = make_issue(title="Python and rust task")
    assert wave.score_issue(issue, CFG) == wave.score_issue(issue, CFG)


# --------------------------------------------------------------------------- #
# draft_text
# --------------------------------------------------------------------------- #


def test_draft_text_includes_profile_and_links():
    text = wave.draft_text(make_issue(title="Python task"), ["python"], CFG)
    assert "Lawal Olayinka Awal" in text
    assert "Ayinkx" in text
    assert "Python Developer" in text
    assert "python" in text
    assert "https://github.com/Ayinkx" in text
    assert "Python task" in text
    assert "Happy to share a short plan." in text


def test_draft_text_falls_back_when_no_skills_matched():
    text = wave.draft_text(make_issue(), [], CFG)
    assert "Python and open-source tooling" in text


# --------------------------------------------------------------------------- #
# state helpers
# --------------------------------------------------------------------------- #


def test_save_and_load_json_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    payload = {"seen": ["a/b#1"], "applied": {"a/b#1": {"ts": "now"}}}
    wave.save_json(path, payload)
    assert wave.load_json(path, {}) == payload
    # on-disk content is valid JSON
    assert json.loads(path.read_text(encoding="utf-8")) == payload


def test_load_json_returns_default_for_missing_file(tmp_path):
    assert wave.load_json(tmp_path / "nope.json", {"fallback": True}) == {"fallback": True}


def test_remaining_slots_subtracts_applied(tmp_path, monkeypatch):
    state = tmp_path / "state.json"
    wave.save_json(state, {"applied": {"a/b#1": {}, "c/d#2": {}}})
    monkeypatch.setattr(wave, "STATE_PATH", state)
    assert wave.remaining_slots(CFG) == CFG["slots"] - 2


def test_remaining_slots_is_never_negative(tmp_path, monkeypatch):
    state = tmp_path / "state.json"
    wave.save_json(state, {"applied": {f"r#{i}": {} for i in range(20)}})
    monkeypatch.setattr(wave, "STATE_PATH", state)
    assert wave.remaining_slots(CFG) == 0
