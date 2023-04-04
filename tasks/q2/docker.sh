aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 879655802347.dkr.ecr.us-east-2.amazonaws.com     
docker build -t tasks .
docker tag tasks:latest 879655802347.dkr.ecr.us-east-2.amazonaws.com/tasks:q2
docker push 879655802347.dkr.ecr.us-east-2.amazonaws.com/tasks:q2
