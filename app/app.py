import json
from collections import defaultdict
from multiprocessing import Pool
import pickle, os
import numpy as np
from scipy.stats import entropy
import sortednp as snp
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

GREY = 0
YELLOW = 1
GREEN = 2

def load_words(length=5):
    words = []
    #for line in s3_client.get_object(Bucket=S3_BUCKET, Key="dictionary.txt")["Body"].read():
    with open('dictionary.txt', 'r') as f:
        for line in f:
            word = line[:-1]
            if len(word) == length:
                words.append(word)
    return words
    
def load_common_words(words, plurals, length=5):
    common_words = []
    #for line in s3_client.get_object(Bucket=S3_BUCKET, Key="20k.txt")["Body"].read():
    with open('20k.txt', 'r') as f:
        for line in f:
            word = line[:-1].upper()
            if len(word) == length and word in words and not word in plurals:
                common_words.append(word)
    return common_words
    
def load_history():
    history = []
    #for line in s3_client.get_object(Bucket=S3_BUCKET, Key="history.txt")["Body"].read():
    with open('history.txt', 'r') as f:
        for line in f:        
            word = line[:-1].upper()
            history.append(word)
    return history    
                    
def occurrences(letter, word):
    count = 0
    for l in word:
        if l == letter:
            count += 1
    return count

def generate_clue(guess, word):
    guessed_letters = ''
    clue = [0,0,0,0,0]
    for i in range(len(guess)):
        if guess[i] == word[i]:
            clue[i] = GREEN
            guessed_letters = guessed_letters + guess[i]
    for i in range(len(guess)):
        if clue[i] == 0 and occurrences(guess[i], word) > occurrences(guess[i], guessed_letters):
            clue[i] = YELLOW
            guessed_letters = guessed_letters + guess[i]
    return tuple(clue)

def see_possibilities_mp(guess, words):
    possibilities = defaultdict(set)
    
    #generated_clues = []
    for word in words:
        clue = generate_clue(guess, word)
        #print(clue, guess, word)
        #generated_clues.append(clue)
        possibilities[clue].add(word)
    return possibilities

def see_possibilities(guess):
    possibilities = defaultdict(set)
    
    for word in words:
        clue = generate_clue(guess, word)
        possibilities[clue].add(word)
    return possibilities



def generate_mapping(filename):
    mapping = {}

    print('generating mapping')
    
    #pool = Pool(os.cpu_count())
    #ps = pool.starmap(see_possibilities_mp, [(word, words) for word in words])
    ps = map(see_possibilities, words)

    for word, p in zip(words, ps):
        mapping[word] = p

    print('done')

    #print(mapping['AERIE'])

    #for word in words:
    #    possibilities = see_possibilities(word, words)
    #    map[word] = possibilities

    print('dumping file')
    pickle.dump(mapping, open(filename, 'wb'))
    print('done')
    
def generate_np_mapping(filename):
	np_mapping = {}
	for word, p in zip(words, map(see_possibilities, words)):
	    np_mapping[word] = {}
	    for key in p.keys():
	        np_mapping[word][key] = create_np_set(sorted(p[key]))
	pickle.dump(np_mapping, open(filename, 'wb'))

def load_mapping(filename):
    return pickle.load(open(filename, 'rb'))

#def load_mapping(object_key):
#    return pickle.load(s3_client.get_object(Bucket=S3_BUCKET, Key=object_key)["Body"].read())

def intersection(s1, s2):
    j = 0
    result = []
    for i in range(len(s1)):
        if j >= len(s2):
            break
        while s1[i] > s2[j]:
            j += 1
        if j >= len(s2):
            break
        if s1[i] == s2[j]:
            result.append(s1[i])
            j += 1
    return result

def measure_min_max(possibilities, possible_words, plurals_np, common_np):
    maximum = 0
    for key in possibilities.keys():
        if key != (2,2,2,2,2):
            intersection = snp.intersect(possibilities[key], possible_words)
            length = len(intersection)
            plurals_length = len(snp.intersect(intersection, plurals_np))
            common_length = len(snp.intersect(intersection, common_np))
            measure = length - (plurals_length * .995) + common_length*100
            if measure > maximum:
                maximum = measure
    return maximum

def measure_entropy(possibilities, possible_words, plurals_np, common_np):
    maximum = 0
    counts = []
    for key in possibilities.keys():
        intersection = snp.intersect(possibilities[key], possible_words)
        length = len(intersection)
        plurals_length = len(snp.intersect(intersection, plurals_np))
        common_length = len(snp.intersect(intersection, common_np))
        measure = length - (plurals_length * 0.995) + common_length*100
        counts.append(measure)
    return entropy(counts, base=2)

def select_word(possible_words, min_max=False, multiprocess=False):
    best_measure = float('inf') if min_max else -float('inf')
    best_word = None
    best_possibilities = None

    if min_max:
        measure = measure_min_max
    else:
        measure = measure_entropy

    if multiprocess:
        pool = Pool(os.cpu_count())
        measures = pool.starmap(measure, ((mapping[word], possible_words, plurals_np, common_np) for word in words))
    else:
        measures = map(measure, (mapping[word] for word in words), (possible_words for word in words), (plurals_np for word in words), (common_np for word in words))

    for i, m in enumerate(measures):
        if snp.isitem(word_to_num(words[i]), possible_words):
            m += min_max*-.51 + 0.01
        if (min_max and m <= best_measure) or (not min_max and m >= best_measure):
            best_measure = m
            best_word = words[i]
    print(best_measure)
    return best_word

def create_np_set(words):
    return np.array(list(map(word_to_num, words)), dtype=np.int16)

def create_np_mapping(mapping, filename):
    np_mapping = {}

    for word in words:
        np_mapping[word] = {}
        for key in mapping[word].keys():
            np_mapping[word][key] = create_np_set(sorted(mapping[word][key]))


    pickle.dump(np_mapping, open(filename, 'wb'))


words = load_words(length=5)
four_letter_words = load_words(length=4)
history = load_history()

plurals = []

for word in four_letter_words:
    if (word + 'S') in words:
        plurals.append(word + 'S')
        
common_words = load_common_words(words, plurals, length=5)
#print(len(common_words))
common_freq_dict = defaultdict(lambda: float("inf"))
for i,word in enumerate(common_words):
	common_freq_dict[word] = i

word_num_dict = {}
for i,word in enumerate(words):
    word_num_dict[word] = i

def word_to_num(word):
    return word_num_dict[word]

def num_to_word(num):
    return words[num]

#print('generating mapping')
#generate_mapping('mapping.p')
#print('done')

#generate_np_mapping('np_mapping.p')


#print('creating np mapping')
#create_np_mapping(mapping, 'np_mapping.p')
#print('done')
        
print('loading mapping')
mapping = load_mapping('np_mapping.p')
second_guess_map = load_mapping('second_guesses.p')
print('done')


plurals_np = create_np_set(sorted(plurals))
common_np = create_np_set(sorted(common_words))

logger.debug('## common_np ##')
logger.debug(common_np)


"""
Empirical results: 2:4, 3: 94, 4: 107, 5: 25, 6: 5
"""	
def guess_wordle(guesses, clues, print_possibilities=False):
    guess = 'RAISE'

    possible_words = create_np_set(sorted(words))

    if len(guesses) == 0:
        return guess, possible_words
    
    for guess, clue in zip(guesses, clues):
        if not clue in mapping[guess].keys():
            possible_words = np.array([], dtype=np.int16);
            break
        possible_words = snp.intersect(possible_words, mapping[guess][clue])

    possible_common_words = snp.intersect(possible_words, common_np)

    if print_possibilities:
        print('POSSIBLE WORDS REMAINING: ' + str(len(possible_words)))
        print(list(map(num_to_word, possible_words)))
        print('POSSIBLE COMMON WORDS REMAINING: ' + str(len(possible_common_words)))
        print(list(map(num_to_word, possible_common_words)))
        print('---------')

    if len(possible_words) == 0:
        guess = None
    elif len(guesses) == 0:
        guess = 'RAISE'
    elif len(guesses) == 1 and guesses[0] == 'RAISE':
        guess = second_guess_map[clues[0]]
    elif len(possible_words) == 2:
        word1 = words[list(possible_words)[0]]
        word2 = words[list(possible_words)[1]]
        if common_freq_dict[word1] <= common_freq_dict[word2]:
            guess = word1
        else:
            guess = word2
    elif len(possible_words) == 1:
        guess = words[list(possible_words)[0]]
    elif len(possible_common_words) == 1:
        guess = words[list(snp.intersect(possible_words, common_np))[0]]
    elif len(possible_common_words) == 2:
        word1 = words[list(possible_common_words)[0]]
        word2 = words[list(possible_common_words)[1]]
        if common_freq_dict[word1] <= common_freq_dict[word2]:
            guess = word1
        else:
            guess = word2
    else:
        guess = select_word(possible_words, min_max=(len(guesses) >= 3))

    return guess, list(map(num_to_word, possible_words))

def handler(event, context):
    logger.info('## ENVIRONMENT VARIABLES')
    logger.info(os.environ)
    logger.debug('## EVENT')
    logger.debug(event)
   
    body = json.loads(event['body'])
    guesses = body['guesses']
    clues = [tuple(clue) for clue in body['clues']]
    
    if len(guesses) != len(clues):
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid request. Length of guesses must match length of clues')
        }

    for guess in guesses:
        if not guess in words:
            return {
                'statusCode': 400,
                'body': json.dumps('Invalid guess. Guess is not in our dictionary.')
            }

    guess, possible_words = guess_wordle(guesses, clues, print_possibilities=False)

    if guess is None:
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid clue. The clue given is not possible given the previous guesses and clues.')
        }
    
    return {
        'statusCode': 200,
        'body': {
            'guess': guess,
            'possible_words': possible_words
        }
    }

