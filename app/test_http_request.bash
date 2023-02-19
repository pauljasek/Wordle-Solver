curl --trace-ascii curl.trace -X POST \
    'https://br7gxujg3p2vooleijh7nuwq2u0tpggb.lambda-url.us-east-1.on.aws/' \
    -H 'Content-Type: application/json' \
    -d '{"guesses": ["RAISE"], "clues": [[0,0,1,0,0]]}'
echo
