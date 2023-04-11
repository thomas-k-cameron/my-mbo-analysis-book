import polars as pl
import boto3
import json

FILES = json.load(open("./files.json", "rb"))["Contents"]
FILES2 = json.load(open("./files2.json", "rb"))["Contents"]
LABEL_V1 = json.load(open("./label_v1.json", "rb"))["Contents"]

def into_dataframe(target_files = 1):
    def func2(i):
        #key = "artifacts/depth_imbalance/0/depth_imbalance_JGBL_100_1000_0.parquet"
        [dateidx, filename] = i["Key"].replace("artifacts/depth_imbalance/", "").split("/")
        i["dateidx"] = int(dateidx)
        [product, depth1, depth2, _dateidx] = filename.replace("depth_imbalance_", "").replace(".parquet", "").split("_")
        i["depth1"] = int(depth1)
        i["depth2"] = int(depth2)
        i["product"] = product

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
    for i in FILES2:
        func2(i)

    if target_files == 1:
        df1, df2 = pl.DataFrame(FILES), pl.DataFrame(LABEL_V1)
    elif target_files == 2:
        df1, df2 = pl.DataFrame(FILES2), pl.DataFrame(LABEL_V1)
    else:
        raise
    
    for i in ["LastModified", "ETag", "Size", "StorageClass"]:
        df1.drop_in_place(i)
        df2.drop_in_place(i)
    print(df1)
    print(df2)
    if "size_thing" in df1.columns:
        df1.drop_in_place("size_thing")

    if target_files == 2:
        _df = df1.join(df2, on=["dateidx", "product"], how="outer").with_columns([pl.col("time_range").cast(pl.Int64), pl.col("size_thing").cast(pl.Int64)])
        return _df.groupby("product").agg([pl.col("Key").alias("data"), pl.col("Key_right").alias("label")])
    else:
        df1_group = df1.groupby(["product", "time_range"]).agg(pl.col("Key"))
        print(df1_group)
        proj = [pl.col("Key").flatten().unique().alias("data"), pl.col("Key_right").unique().alias("labels")]
        _df2 = df1_group.join(df2, on=["product"]).groupby(["product", "time_range", "size_thing"]).agg(proj)
        print(_df2)
        return _df2

df = into_dataframe()

CLIENT = boto3.client("batch")

plots = ["plot_near_expiration_target_products"]


print(df)
def target2():
    df = into_dataframe(2)
    hashmap = {}
    for dic in df.to_dicts():
        dic["data"] = list(set(dic["data"]))
        dic["label"] = list(set(dic["label"]))
        hashmap[dic["product"]] = dic
    
    hashmap["NK225M"]["label"] = hashmap["NK225"]["label"]
    hashmap["TOPIXM"]["label"] = hashmap["TOPIX"]["label"]
    
    for key in hashmap.keys():
        dic = hashmap[key]
        env = []
        jobName = []
        for i in dic.keys():
            if isinstance(dic[i], list):
                val = " ".join(dic[i])
            else:
                val = dic[i]
                jobName.append(dic[i])
            env.append({"name": i.upper(), "value": val})
        
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

def target1():
    df = into_dataframe(1)
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

target2()