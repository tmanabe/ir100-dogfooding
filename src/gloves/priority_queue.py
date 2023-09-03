import heapq


# 2.1
class PriorityQueue(object):
    def __init__(self, size):
        assert 0 < size
        self.body = []
        self.size = size

    def peek(self):
        return self.body[0]

    def push(self, item):
        if len(self.body) < self.size:
            heapq.heappush(self.body, item)
        else:
            if self.peek() < item:
                heapq.heappushpop(self.body, item)

    def pop(self):
        return heapq.heappop(self.body)


# 6.2
class BatchPriorityQueue(object):  # For batch processing of multiple queries
    def __init__(self, sizes):
        self.priority_queues = [PriorityQueue(size) for size in sizes]

    def batch_push(self, priority_matrix, items):
        assert len(priority_matrix) == len(items)
        for priorities, item in zip(priority_matrix, items):
            assert len(self.priority_queues) == len(priorities)
            for priority_queue, priority in zip(self.priority_queues, priorities):
                priority_queue.push((priority, item))

    def batch_pop(self):
        results = []
        for priority_queue in self.priority_queues:
            result = []
            while 0 < len(priority_queue.body):
                result.append(priority_queue.pop())
            result.reverse()
            results.append(result)
        return results
