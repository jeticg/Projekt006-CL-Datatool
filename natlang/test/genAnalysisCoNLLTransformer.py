import random

random.seed(10)


def generate(maxDepth=10, maxLength=10):
    entry = []
    string = ""
    if maxDepth == 0:
        number = str(int(20 * random.random()))
        entry.append(number)
        string += '(' + number + ')'
        return entry, string
    depth = random.randint(1, maxDepth)
    length = random.randint(1, maxLength)
    print("Depth:", depth, "; Length:", length)

    for i in range(length):
        if random.random() > 0.5:
            number = str(int(20 * random.random()))
            entry.append(number)
            string += ' ' + number + ' '

        else:
            newEntry, newString = generate(maxDepth=depth - 1,
                                           maxLength=maxLength)
            entry.append(newEntry)
            string += ' ' + newString + ' '
    return entry, '(' + string + ')'
