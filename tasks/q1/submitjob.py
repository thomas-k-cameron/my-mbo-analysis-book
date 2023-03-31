import boto3
CLIENT = boto3.client("batch")

plots = ["plot_near_expiration_target_products"]

for i in plots:
    response = CLIENT.submit_job(
        jobName="this",
        jobQueue='amd8cpu-ram60gb-storage100gb',
        jobDefinition='arn:aws:batch:us-east-2:879655802347:job-definition/mlimage1:4',
        containerOverrides={
            'command': [
                'python3', '/root/main.py'
            ],
            'environment': [
                {"name": "PLOT", "value": i}
            ],
        }
    )
    jobid = response['jobId']

    print(response)