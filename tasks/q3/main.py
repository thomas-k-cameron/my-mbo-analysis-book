# %%
import polars as pl
import seaborn as sns
import os 
import boto3 

PRODUCT = os.environ["PRODUCT"]
DEPTH1 = os.environ["DEPTH1"]
DEPTH2 = os.environ["DEPTH2"]
DATA = os.environ["DATA"]

KEY=f"{PRODUCT}_{DEPTH1}_{DEPTH2}"

BUCKET_NAME="compute-assets-36607b9c2d934caa8bf7d19e0251bab6"
S3_CONNECT = boto3.client("s3")

def load_data():
    df = None
    labeldf: dict[str, pl.DataFrame] = {}
    for i in os.listdir("/tmp/input"):
        if i.endswith(".csv"):
            _df = pl.read_csv("/tmp/input/"+i)
        else:
            _df = pl.read_parquet("/tmp/input/"+i)
        if "depth_imbalance_" in i:
            if isinstance(df, pl.DataFrame):
                df = df.vstack(_df.select(df.columns), in_place=True)
            else:
                df = _df

            df.shrink_to_fit(in_place=True)
        else:
            [_product, signal_size, _, _dateidx_csv] = i.split("_")
            _df = _df.select([pl.col("base_timestamp").str.strptime(pl.Datetime("ns")).alias("timestamp"), pl.col("signal")]).select(pl.col("*").suffix(f"_{signal_size}"))
            if signal_size in labeldf:
                labeldf[signal_size] = labeldf[signal_size].vstack(_df.select(labeldf[signal_size].columns), in_place=True)
            else:
                labeldf[signal_size] = _df

            labeldf[signal_size].shrink_to_fit(in_place=True)

    keys = list(labeldf.keys())
    _labeldf = labeldf[keys[0]].lazy().join(labeldf[keys[1]].lazy(), on="timestamp").join(labeldf[keys[2]].lazy(), on="timestamp")

    assert isinstance(df, pl.DataFrame)
    print("joining")
    cols = []
    for i in df.columns:
        col = pl.col(i)
        if "spread" in i:
            col = col.alias("spread")
        elif "ask" in i:
            col = col.alias("ask")
        elif "bid" in i:
            col = col.alias("bid")
        else:
            continue

    cols.append(pl.col(["timestamp", "signal"]))
    df2 = _labeldf.lazy().join(df.lazy(), on="timestamp", how="outer").select(cols).sort("timestamp")
    df2 = df2.with_columns(pl.col("signal").cast(pl.Categorical).forward_fill()).drop_nulls()
    df2 = df2.sort("timestamp").with_columns(pl.col("timestamp").shift_and_fill(1, 0).alias("time_delta").cast(pl.Datetime("ns"))-pl.col("timestamp")).with_columns(pl.col("time_delta").abs())
    return df2.drop_nulls().filter(pl.col("time_delta").abs() > (pl.col("time_delta")+pl.duration(hours=1))).sort("timestamp")



def main():
    df = load_data().collect()
    outfile = "/tmp/output/file.parquet"
    df.write_parquet(outfile, compression_level=18, compression="zstd")
    S3_CONNECT.put_object(Body=open(outfile, "rb"), Bucket="compute-assets-36607b9c2d934caa8bf7d19e0251bab6", Key=f"artifacts/depth-imbalance-spread/{KEY}.parquet")

main()