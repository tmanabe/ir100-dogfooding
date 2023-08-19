from math import log2


ESCI_LABEL_TO_GAIN = {
    "E": 4,
    "S": 2,
    "C": 1,
    "I": 0,
}


def calc_dcgs_at(k, rankings):
    dcgs = []
    last_query_id, rank, dcg = None, 0, 0.0
    for query_id, esci_label in zip(rankings["query_id"], rankings["esci_label"]):
        if last_query_id != query_id:
            if last_query_id is not None:
                dcgs.append(dcg)
            last_query_id, rank, dcg = query_id, 0, 0.0
        rank += 1
        if rank <= k:
            dcg += ESCI_LABEL_TO_GAIN[esci_label] / log2(rank + 1)
    if last_query_id is not None:
        dcgs.append(dcg)
    return dcgs


def calc_ndcgs(dcgs, ideal_dcgs):
    assert len(dcgs) == len(ideal_dcgs)
    ndcgs = []
    for dcg, ideal_dcg in zip(dcgs, ideal_dcgs):
        if 0 < ideal_dcg:
            ndcgs.append(dcg / ideal_dcg)
    return ndcgs
