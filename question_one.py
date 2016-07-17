import random
import numpy as np

# class for each postion on the keypad
class Key:
    def __init__(self, name, value, moves):
        self.name = name
        self.value = value
        self.moves = moves

#initiallize value for each key and the possible moves
one = Key('one', 1, ["six", "seven"])
two = Key('two', 2,["seven", "nine"])
three = Key('three', 3, ["four", "eight"])
four = Key('four', 4,["three", "nine", "zero"])
# five have no moves, and will not be moved to either
six = Key('six', 6,["one", "seven", "zero"])
seven = Key('seven', 7, ["two", "six"])
eight = Key('eight', 8, ["one", "three"])
nine = Key('nine', 9, ["two", "four"])
zero = Key('zero', 0, ["four", "six"])

# dictionary for each key by name
dict = {'one': one, 'two':two, 'three':three, 'four':four, 'six':six, 'seven':seven, 'eight':eight, 'nine':nine, 'zero':zero}

# initial vairables
move_count = 0
move_sum = 0;
current_pos = zero

# move function, re-assign current after moved, tally sum and count, return current position
def move(current, count, sum):
    movedto = random.randint(0, len(current.moves)-1)
    next = current.moves[movedto]
    current = dict[next]
    count += 1
    sum += current.value
    return current, count, sum

# put all results in list and use numpy to calculate stats
list = []
prob = [] # probability
by_seven = 0.0
by_five = 0.0

# repeat 1000 times to get reasonable stats
for j in range(100001):
    # change the range to either 10 or 1024 according to question
    for i in range(1024):
        [current_pos, move_count, move_sum] = move(current_pos, move_count, move_sum)
        mod = move_sum % 1024
        list.append(mod)
        
    # find probability, change to 23 given 29
    if (move_sum % 29 == 0):
        by_seven += 1
        if (move_sum % 23 == 0):
            by_five += 1
    if (by_seven > 0):
        prob.append(by_five/by_seven)
            
print 'probability of divisible by 5 given it is divisible by 7', np.mean(prob)
print 'S mod 10 mean', np.mean(list)
# use double precision for standard deviation
print 'S mod 10 standard deviation', np.std(list, dtype=np.float64)
