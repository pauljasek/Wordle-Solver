import app, json

result =  app.handler({'body': json.dumps({'guesses': ['RAISE'], 'clues': [[2,2,2,2,0]]})}, None)
#result = app.guess_wordle(["RAISE"], [(2,2,2,2,0)]);
print(result)