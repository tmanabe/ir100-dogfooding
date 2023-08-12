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


def parse_and(and_term):
    result = None
    for word in and_term.split():
        if result is None:
            result = WordQuery(word)
        else:
            result = BooleanAndQuery(result, WordQuery(word))
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
