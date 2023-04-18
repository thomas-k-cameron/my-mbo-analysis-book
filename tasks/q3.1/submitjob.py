import boto3
import json

s3conn = boto3.client("s3")
batchconn = boto3.client("batch")

try:
    contents = json.load(open("taskq3.1.json", "r"))
except:
    response: dict = s3conn.list_objects_v2(
            Bucket='compute-assets-36607b9c2d934caa8bf7d19e0251bab6',
            Prefix='artifacts/depth-imbalance-spread/',
    )
    contents = response["Contents"]
    contents = list(map(lambda x: x["Key"], contents))

contents.sort()

JGBL_SIGNAL = [
    'signal_500',
    'signal_150',
    'signal_300',
]
NK225_SIGNAL = ['signal_1000000',
 'signal_2500000',
 'signal_500000',]

TOPIX_SIGNAL = ['signal_15000',
                'signal_50000',
                'signal_30000',
                ]


def main():
    env = []
    for key in reversed(contents):
        env.append({"name": "FILE", "value": key})
        print(key)
        signal = NK225_SIGNAL
        if "JGBL" in key:
            signal = JGBL_SIGNAL
        elif "TOPIX" in key:
            signal = TOPIX_SIGNAL

        env.append({"name": "SIGNAL", "value": " ".join(signal)})

        jobDefinition = "arn:aws:batch:us-east-2:879655802347:job-definition/4cpu-30gb:6"
        jobQueue = "amd4cpu-ram30gb-storage100gb"
        resp = batchconn.submit_job(
            jobName="q3_1__"+key.split("/")[-1].replace(".parquet", ""),
            jobQueue=jobQueue,
            jobDefinition=jobDefinition,
            containerOverrides={
                'environment': env,
                'command': [
                    'bash', '/root/main.sh'
                ],
                'environment': env,
            }
        )
        jobid = resp['jobId']
        print(jobid)

main()
