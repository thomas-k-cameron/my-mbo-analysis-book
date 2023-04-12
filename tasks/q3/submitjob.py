import polars as pl
import boto3
import json


CLIENT = boto3.client("batch")

plots = ["plot_near_expiration_target_products"]

FILES = json.load(open("./files2.json", "rb"))["Contents"]
LABEL_V1 = json.load(open("./label_v1.json", "rb"))["Contents"]

def into_dataframe():
    def func2(i):
        #key = "artifacts/depth_imbalance/0/depth_imbalance_JGBL_100_1000_0.parquet"
        [dateidx, filename] = i["Key"].replace("artifacts/depth_imbalance/", "").split("/")
        i["dateidx"] = int(dateidx)
        [product, depth1, depth2, _dateidx] = filename.replace("depth_imbalance_", "").replace(".parquet", "").split("_")
        i["depth1"] = int(depth1)
        i["depth2"] = int(depth2)
        i["product"] = product

    def label(i):
        key = i["Key"]
        [product, signal_size, _, date_idx_with_suffix] = key.replace("artifacts/labels_v1/", "").split("_")
        i["dateidx"] = int(date_idx_with_suffix.replace(".csv.zst", ""))
        i["product"] = product
        i["signal_size"] = int(signal_size)

    for i in LABEL_V1:
        label(i)
    for i in FILES:
        func2(i)

    df1, df2 = pl.DataFrame(FILES).with_columns(pl.col("product").str.to_uppercase()), pl.DataFrame(LABEL_V1).with_columns(pl.col("product").str.to_uppercase())
    for i in ["LastModified", "ETag", "Size", "StorageClass"]:
        df1.drop_in_place(i)
        df2.drop_in_place(i)
    print(df1)
    print(df2)

    if "size_thing" in df1.columns:
        df1.drop_in_place("size_thing")

    def _main(product1, product2):
        _df2 = df2.filter(pl.col("product") == product1)
        return _df2.with_columns(pl.repeat(product2, _df2.height, eager = True, name ="product"))

    df2 = df2.vstack(_main("NK225", "NK225M").select(df2.columns)).vstack(_main("TOPIX", "TOPIXM").select(df2.columns)).sort("product")
    print(df2)
    _df1 = df1.groupby([pl.col("product"), pl.col("depth1"), pl.col("depth2")]).agg(pl.col("*")).sort(["product", "depth1", "depth2"])
    _df2 = df2.groupby(["product"]).agg([pl.col("Key")])
    print(_df2)
    _df = _df1.join(_df2, on=["product"], how="outer")
    _df = _df.groupby(["product", "depth1", "depth2"]).agg([pl.col("Key").alias("data").flatten(), pl.col("Key_right").alias("label").flatten()])
    _df = _df.select([pl.col("*").exclude(["label", "data"]), pl.col("label").arr.unique(), pl.col("data").arr.unique()])
    return _df

def main():
    df = into_dataframe()
    print(df)

    hashmap = {}
    stack = []
    for dic in df.to_dicts():
        dataset = set(dic["data"])
        if None in dataset:
            dataset.remove(None)
        dic["data"] = list(dataset)
        labelset = set(dic["label"])
        if None in labelset:
            labelset.remove(None)
        dic["label"] = list(labelset)
        stack.append(dic)
        
    for dic in stack:
        env = []
        jobName = []
        for i in dic.keys():
            if isinstance(dic[i], list):
                val = " ".join(dic[i])
            else:
                val = dic[i]
                jobName.append(str(dic[i]))
            env.append({"name": i.upper(), "value": str(val)})
        
        jobDefinition = "arn:aws:batch:us-east-2:879655802347:job-definition/fargate_best_spec:3"
        jobQueue= "fargate"
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
        
main()