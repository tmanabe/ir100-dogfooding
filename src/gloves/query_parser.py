from gloves.query import BooleanAndQuery
from gloves.query import BooleanOrQuery
from gloves.query import PhraseQuery
from gloves.query import Query
from gloves.query import WordQuery


QUOTE = '"'
AND = "AND"
OR = "OR"
KAKKO = "("
KOKKA = ")"
META = {
    QUOTE,
    AND,
    OR,
    KAKKO,
    KOKKA,
}


class QueryParser(object):
    @classmethod
    def merge_and(cls, input):
        i, output = 0, []
        while i < len(input):
            if i + 1 < len(input) and isinstance(input[i], Query) and isinstance(input[i + 1], Query):
                output.append(BooleanAndQuery(input[i], input[i + 1]))
                i += 2
            else:
                output.append(input[i])
                i += 1
        return output

    @classmethod
    def merge_phrase(cls, input):
        i, output = 0, []
        while i < len(input):
            if i + 2 < len(input) and input[i] == QUOTE and isinstance(input[i + 1], Query) and input[i + 2] == QUOTE:
                output.append(PhraseQuery(input[i + 1]))
                i += 3
            else:
                output.append(input[i])
                i += 1
        return output

    @classmethod
    def merge_or(cls, input):
        i, output = 0, []
        while i < len(input):
            if (
                i + 2 < len(input)
                and isinstance(input[i], Query)
                and input[i + 1] == OR
                and isinstance(input[i + 2], Query)
            ):
                output.append(BooleanOrQuery(input[i], input[i + 2]))
                i += 3
            else:
                output.append(input[i])
                i += 1
        return output

    @classmethod
    def merge_kakko_kokka(cls, input):
        i, output = 0, []
        while i < len(input):
            if i + 2 < len(input) and input[i] == KAKKO and isinstance(input[i + 1], Query) and input[i + 2] == KOKKA:
                output.append(input[i + 1])
                i += 3
            else:
                output.append(input[i])
                i += 1
        return output

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def parse(self, string):
        buffer, in_quote = [], False
        for word in self.tokenizer(string):
            if word == QUOTE:
                buffer.append(word)
                in_quote = not in_quote
            elif word in META:
                if in_quote:
                    buffer.append(WordQuery(word))
                else:
                    buffer.append(word)
            else:
                buffer.append(WordQuery(word))
        while 1 < len(buffer):
            while True:
                output = self.merge_and(buffer)
                if output == buffer:
                    break
                buffer = output
            buffer = self.merge_phrase(buffer)
            while True:
                output = self.merge_or(buffer)
                if output == buffer:
                    break
                buffer = output
            while True:
                output = self.merge_kakko_kokka(buffer)
                if output == buffer:
                    break
                buffer = output
        return buffer[0]
