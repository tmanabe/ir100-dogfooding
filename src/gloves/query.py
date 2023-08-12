from gloves.iterator import expanded_boolean_and
from gloves.iterator import expanded_boolean_or


class WordQuery(object):
    def __init__(self, word):
        self.word = word

    def iterator(self, inverted_index):
        return inverted_index.iter(self.word)


# 4.1
class BooleanAndQuery(object):
    def __init__(self, query_i, query_j):
        self.query_i = query_i
        self.query_j = query_j

    def iterator(self, inverted_index):
        iterator_i = self.query_i.iterator(inverted_index)
        iterator_j = self.query_j.iterator(inverted_index)
        return expanded_boolean_and(iterator_i, iterator_j)


# 4.7
class BooleanOrQuery(object):
    def __init__(self, query_i, query_j):
        self.query_i = query_i
        self.query_j = query_j

    def iterator(self, inverted_index):
        iterator_i = self.query_i.iterator(inverted_index)
        iterator_j = self.query_j.iterator(inverted_index)
        return expanded_boolean_or(iterator_i, iterator_j)


# 4.9
def phrase_match(pair):
    _, expansions = pair
    indices = [0] * (len(expansions) - 1)
    for start in expansions[0].positions:
        success = True
        for offset, expansion in enumerate(expansions[1:]):
            target = start + offset + 1
            while expansion.positions[indices[offset]] < target:
                indices[offset] += 1
                if len(expansion.positions) <= indices[offset]:
                    return False
            if target < expansion.positions[indices[offset]]:
                success = False
                break
        if success:
            return True
    return False


class PhraseQuery(object):
    def __init__(self, boolean_and_query):
        self.boolean_and_query = boolean_and_query

    def iterator(self, inverted_index):
        return filter(phrase_match, self.boolean_and_query.iterator(inverted_index))


def parse_and(and_term):
    result = None
    in_phrase, in_phrase_result = False, None
    for word in and_term.split():
        if '"' == word:
            if in_phrase:
                assert isinstance(in_phrase_result, BooleanAndQuery)  # means multiple words in the phrase
                if result is None:
                    result = PhraseQuery(in_phrase_result)
                else:
                    result = BooleanAndQuery(result, PhraseQuery(in_phrase_result))
                in_phrase, in_phrase_result = False, None
            else:
                in_phrase = True
        else:
            if in_phrase:
                if in_phrase_result is None:
                    in_phrase_result = WordQuery(word)
                else:
                    in_phrase_result = BooleanAndQuery(in_phrase_result, WordQuery(word))
            else:
                if result is None:
                    result = WordQuery(word)
                else:
                    result = BooleanAndQuery(result, WordQuery(word))
    assert not in_phrase and in_phrase_result is None
    return result


def parse_or(or_term):
    result = None
    for and_term in or_term.split(" OR "):
        if result is None:
            result = parse_and(and_term)
        else:
            result = BooleanOrQuery(result, parse_and(and_term))
    return result


def parse(query):
    return parse_or(query)
