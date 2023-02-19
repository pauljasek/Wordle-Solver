sudo docker build -t wordle-solver .
aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin 085560674184.dkr.ecr.us-east-1.amazonaws.com
sudo docker tag wordle-solver:latest 085560674184.dkr.ecr.us-east-1.amazonaws.com/wordle-solver:latest
sudo docker push 085560674184.dkr.ecr.us-east-1.amazonaws.com/wordle-solver:latest
