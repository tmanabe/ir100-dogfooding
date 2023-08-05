from Stemmer import Stemmer
from regex import split
from uniseg.wordbreak import words


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


# 7.5
def unicode_text_segmentation_tokenizer(string):
    return words(string)
