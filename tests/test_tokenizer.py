from search_engine.tokenizer.tokenizer import tokenize


def test_lowercases_and_strips_punctuation():
    assert tokenize("Hello, World!") == ["hello", "world"]


def test_removes_stopwords():
    assert tokenize("the cat is on the mat") == ["cat", "mat"]


def test_keeps_stopwords_when_disabled():
    result = tokenize("the cat is on the mat", remove_stopwords=False)
    assert "the" in result
