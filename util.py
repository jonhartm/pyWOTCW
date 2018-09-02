import time

# try to parse a string to an int.
# returns None if it failed
def tryParseInt(s):
    try:
        return (int(s))
    except Exception:
        return None

# class for starting and stopping a timer, then reporting the elapsed time
class Timer():
    def Start(self):
        self.start = time.time()

    def Stop(self):
        self.end = time.time()
        self.elapsed = self.end-self.start

    def __str__(self):
        return '{:.3}s'.format(self.elapsed)

# parses a list of lists and returns a dictionary based on the key index
# e.g. func([[1,A,2][2,A,4]], 1) would return {A:[[1,A,2][2,A,4]]}
def getDictFromListWithIndex(item_list, key_index):
    new_dict = {}
    for item in item_list:
        item = list(item)
        if item[key_index] not in new_dict:
            new_dict[item[key_index]] = []
        index = item.pop(key_index)
        new_dict[index].append(item)
    return sorted(new_dict.items())
