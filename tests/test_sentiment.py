from sentiment import analyse_text, clean_text, score_sentence


def test_clean_text_removes_url_and_punctuation():
    assert clean_text("Strong gain! https://example.com").strip() == "strong gain"


def test_positive_sentence_scores_above_zero():
    assert score_sentence("strong growth and record profit") > 0


def test_negation_flips_positive_word():
    assert score_sentence("not strong") < 0


def test_analyse_text_labels_positive_content():
    result = analyse_text("Company reports strong growth and record profit.")
    assert result["label"] == "positive"
    assert result["score"] > 0


def test_analyse_text_empty_is_neutral():
    result = analyse_text("")
    assert result["label"] == "neutral"
    assert result["score"] == 0.0
