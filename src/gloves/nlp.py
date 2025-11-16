from MeCab import Tagger
from Stemmer import Stemmer
from regex import compile
from regex import split


def as_is_tokenizer(string):
    return iter([string])


def whitespace_tokenizer(string):
    return iter(string.split())


# 7.1
def english_possessive_filter(iterator):
    for word in iterator:
        if word.endswith("'"):
            yield word[:-1]
        elif word.endswith("'s"):
            yield word[:-2]
        else:
            yield word


# 7.2
def english_lowercase_filter(iterator):
    for word in iterator:
        yield word.lower()


# 7.3
porter_stemmer = Stemmer("porter")


def porter_stem_filter(iterator):
    for word in iterator:
        yield porter_stemmer.stemWord(word)


# 7.4
def unicode_punctuation_tokenizer(string):
    return iter(split(r"\p{P}+", string))


# 7.6
tagger_wakati = Tagger("-Owakati")


def mecab_tokenizer(string):
    node = tagger_wakati.parseToNode(string)
    while node:
        yield node.surface
        node = node.next


# 7.7
tagger = Tagger()


def mecab_analyzer(string):
    node = tagger.parseToNode(string)
    while node:
        yield node
        node = node.next


POS_TO_FILTER = {
    "接続詞",
    "助詞",
    "助動詞",
}


def pos_filter(node_iterator):
    for node in node_iterator:
        pos = node.feature.split(",", 1)[0]
        if pos not in POS_TO_FILTER:
            yield node.surface


# 7.8
katakana_stem_pattern = compile(r"^(\p{Katakana}{3,})ー$")


def katakana_stem_filter(iterator):
    for word in iterator:
        yield katakana_stem_pattern.sub(word, r"\1")
