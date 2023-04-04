import polars as pl
import boto3
import json

FILES = json.load(open("./files.json", "rb"))["Contents"]
LABEL_V1 = json.load(open("./label_v1.json", "rb"))["Contents"]

def into_dataframe():
    def func(i):
        arr = i["Key"].split("_")
        
        dateidx = arr[len(arr)-1].replace(".csv.zst", "")
        i["dateidx"] = int(dateidx)
        
        product = i["Key"].split("/")[2].replace("synthetic_taker_positions_", "").split("_")[0].upper()
        i["product"] = product

        timerange_arr = i["Key"].split("/")[2].replace("synthetic_taker_positions_", "").split("_")
        i["time_range"] = timerange_arr[len(timerange_arr)-2]

        size_thing = i["Key"].split("/")[2].replace("synthetic_taker_positions_", "").split("_")
        i["size_thing"] = size_thing[1]

    for i in LABEL_V1:
        func(i)
    for i in FILES:
        func(i)

    df1, df2 = pl.DataFrame(FILES), pl.DataFrame(LABEL_V1)
    for i in ["LastModified", "ETag", "Size", "StorageClass"]:
        df1.drop_in_place(i)
        df2.drop_in_place(i)

    df1.drop_in_place("size_thing")
    
    df1_group = df1.groupby(["product", "time_range"]).agg(pl.col("Key"))
    print(df1_group)
    _df2 = df1_group.join(df2, on=["product"]).groupby(["product", "time_range", "size_thing"]).agg([pl.col("Key").flatten().unique().alias("data"), pl.col("Key_right").unique().alias("labels")])
    print(_df2)
    return _df2

df = into_dataframe()

CLIENT = boto3.client("batch")

plots = ["plot_near_expiration_target_products"]


print(df)

for dic in df.to_dicts():
    env = []
    jobName = []
    for i in dic.keys():
        
        if isinstance(dic[i], list):
            val = " ".join(dic[i])
        else:
            val = dic[i]
            jobName.append(dic[i])
        env.append({"name": i.upper(), "value": val})
    
    
    
    if "TOPIX" == dic["product"]:
        jobDefinition = "arn:aws:batch:us-east-2:879655802347:job-definition/cpu32-256ram:5"
        jobQueue = "r6g-8xlarge"
    else:
        jobDefinition = "arn:aws:batch:us-east-2:879655802347:job-definition/fargate_best_spec:2"
        jobQueue= "fargate"
    
    print(jobQueue, jobDefinition)
    response = CLIENT.submit_job(
        jobName="_".join(jobName),
        jobQueue=jobQueue,
        jobDefinition=jobDefinition,
        containerOverrides={
            'command': [
                'bash', '/root/main.sh'
            ],
            'environment': env,
        }
    )
    jobid = response['jobId']
    print(jobid)