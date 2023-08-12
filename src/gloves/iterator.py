# 1.5
def boolean_and(iterator_i, iterator_j):
    try:
        entry_i = next(iterator_i)
        entry_j = next(iterator_j)
        while True:
            if entry_i < entry_j:
                entry_i = next(iterator_i)
            elif entry_j < entry_i:
                entry_j = next(iterator_j)
            else:
                yield entry_i
                entry_i = next(iterator_i)
                entry_j = next(iterator_j)
    except StopIteration:
        return


# 1.6
def boolean_or(iterator_i, iterator_j):
    try:
        entry_i = next(iterator_i)
    except StopIteration:
        for entry_j in iterator_j:
            yield entry_j
        return
    try:
        entry_j = next(iterator_j)
    except StopIteration:
        yield entry_i
        for entry_i in iterator_i:
            yield entry_i
        return
    while True:
        if entry_i < entry_j:
            yield entry_i
            try:
                entry_i = next(iterator_i)
            except StopIteration:
                yield entry_j
                for entry_j in iterator_j:
                    yield entry_j
                return
        elif entry_j < entry_i:
            yield entry_j
            try:
                entry_j = next(iterator_j)
            except StopIteration:
                yield entry_i
                for entry_i in iterator_i:
                    yield entry_i
                return
        else:
            yield entry_i
            try:
                entry_i = next(iterator_i)
            except StopIteration:
                for entry_j in iterator_j:
                    yield entry_j
                return
            try:
                entry_j = next(iterator_j)
            except StopIteration:
                yield entry_i
                for entry_i in iterator_i:
                    yield entry_i
                return


# 1.7
def boolean_and_not(iterator_i, iterator_j):
    try:
        entry_i = next(iterator_i)
    except StopIteration:
        return
    try:
        entry_j = next(iterator_j)
    except StopIteration:
        yield entry_i
        for entry_i in iterator_i:
            yield entry_i
        return
    while True:
        if entry_i < entry_j:
            yield entry_i
            try:
                entry_i = next(iterator_i)
            except StopIteration:
                return
        elif entry_j < entry_i:
            try:
                entry_j = next(iterator_j)
            except StopIteration:
                yield entry_i
                for entry_i in iterator_i:
                    yield entry_i
                return
        else:
            try:
                entry_i = next(iterator_i)
            except StopIteration:
                return
            try:
                entry_j = next(iterator_j)
            except StopIteration:
                yield entry_i
                for entry_i in iterator_i:
                    yield entry_i
                return


# 2.2
def extended_boolean_or(iterator_i, iterator_j):
    try:
        entry_i = next(iterator_i)
    except StopIteration:
        for entry_j in iterator_j:
            yield entry_j[0], 0, entry_j[1]
        return
    try:
        entry_j = next(iterator_j)
    except StopIteration:
        yield entry_i[0], entry_i[1], 0
        for entry_i in iterator_i:
            yield entry_i[0], entry_i[1], 0
        return
    while True:
        if entry_i[0] < entry_j[0]:
            yield entry_i[0], entry_i[1], 0
            try:
                entry_i = next(iterator_i)
            except StopIteration:
                yield entry_j[0], 0, entry_j[1]
                for entry_j in iterator_j:
                    yield entry_j[0], 0, entry_j[1]
                return
        elif entry_j[0] < entry_i[0]:
            yield entry_j[0], 0, entry_j[1]
            try:
                entry_j = next(iterator_j)
            except StopIteration:
                yield entry_i[0], entry_i[1], 0
                for entry_i in iterator_i:
                    yield entry_i[0], entry_i[1], 0
                return
        else:
            yield entry_i[0], entry_i[1], entry_j[1]
            try:
                entry_i = next(iterator_i)
            except StopIteration:
                for entry_j in iterator_j:
                    yield entry_j[0], 0, entry_j[1]
                return
            try:
                entry_j = next(iterator_j)
            except StopIteration:
                yield entry_i[0], entry_i[1], 0
                for entry_i in iterator_i:
                    yield entry_i[0], entry_i[1], 0
                return


# 4.1
def expanded_boolean_and(iterator_i, iterator_j):
    try:
        entry_i = next(iterator_i)
        entry_j = next(iterator_j)
        while True:
            if entry_i[0] < entry_j[0]:
                entry_i = next(iterator_i)
            elif entry_j[0] < entry_i[0]:
                entry_j = next(iterator_j)
            else:
                yield entry_i[0], entry_i[1] + entry_j[1]
                entry_i = next(iterator_i)
                entry_j = next(iterator_j)
    except StopIteration:
        return


# 4.7
def expanded_boolean_or(iterator_i, iterator_j):
    try:
        entry_i = next(iterator_i)
    except StopIteration:
        for entry_j in iterator_j:
            yield entry_j[0], [None] + entry_j[1]
        return
    try:
        entry_j = next(iterator_j)
    except StopIteration:
        yield entry_i[0], entry_i[1] + [None]
        for entry_i in iterator_i:
            yield entry_i[0], entry_i[1] + [None]
        return
    while True:
        if entry_i[0] < entry_j[0]:
            yield entry_i[0], entry_i[1] + [None]
            try:
                entry_i = next(iterator_i)
            except StopIteration:
                yield entry_j[0], [None] + entry_j[1]
                for entry_j in iterator_j:
                    yield entry_j[0], [None] + entry_j[1]
                return
        elif entry_j[0] < entry_i[0]:
            yield entry_j[0], [None] + entry_j[1]
            try:
                entry_j = next(iterator_j)
            except StopIteration:
                yield entry_i[0], entry_i[1] + [None]
                for entry_i in iterator_i:
                    yield entry_i[0], entry_i[1] + [None]
                return
        else:
            yield entry_i[0], entry_i[1] + entry_j[1]
            try:
                entry_i = next(iterator_i)
            except StopIteration:
                for entry_j in iterator_j:
                    yield entry_j[0], [None] + entry_j[1]
                return
            try:
                entry_j = next(iterator_j)
            except StopIteration:
                yield entry_i[0], entry_i[1] + [None]
                for entry_i in iterator_i:
                    yield entry_i[0], entry_i[1] + [None]
                return
