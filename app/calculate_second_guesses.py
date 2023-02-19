import app
import pickle

possible_clues = []
for a in range(3):
    for b in range(3):
        for c in range(3):
            for d in range(3):
                for e in range(3):
                    possible_clues.append((a,b,c,d,e))

first_guess = app.guess_wordle([], [])
guess_map = {}
for clue in possible_clues:
    guess_map[clue] = app.guess_wordle([first_guess], [clue])
    print(clue, guess_map[clue])

print(guess_map)

pickle.dump(guess_map, open('second_guesses.p', 'wb'))