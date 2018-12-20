import sys, time

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

# adapted from http://code.activestate.com/recipes/577058/
def query_yes_no(question, default=None):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes":True,   "y":True,
             "no":False,     "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while 1:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return default
        elif choice in valid.keys():
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")
