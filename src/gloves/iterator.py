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


def boolean_or(iterator_i, iterator_j):
    try:
        entry_i = next(iterator_i)
    except StopIteration:
        while True:
            try:
                yield next(iterator_j)
            except StopIteration:
                return
    try:
        entry_j = next(iterator_j)
    except StopIteration:
        yield entry_i
        while True:
            try:
                yield next(iterator_i)
            except StopIteration:
                return
    while True:
        if entry_i < entry_j:
            yield entry_i
            try:
                entry_i = next(iterator_i)
            except StopIteration:
                yield entry_j
                while True:
                    try:
                        yield next(iterator_j)
                    except StopIteration:
                        return
        else:
            yield entry_j
            try:
                entry_j = next(iterator_j)
            except StopIteration:
                yield entry_i
                while True:
                    try:
                        yield next(iterator_i)
                    except StopIteration:
                        return


def boolean_and_not(iterator_i, iterator_j):
    try:
        entry_i = next(iterator_i)
    except StopIteration:
        return
    try:
        entry_j = next(iterator_j)
    except StopIteration:
        yield entry_i
        while True:
            try:
                yield next(iterator_i)
            except StopIteration:
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
                while True:
                    try:
                        yield next(iterator_i)
                    except StopIteration:
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
                while True:
                    try:
                        yield next(iterator_i)
                    except StopIteration:
                        return
