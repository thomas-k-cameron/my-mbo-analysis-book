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
    signal_cols = set()
    labeldf: dict[str, pl.DataFrame] = {}
    for i in os.listdir("/tmp/input"):
        if i.endswith(".csv"):
            [_product, signal_size, _, _dateidx_csv] = i.split("_")
            _df = pl.read_csv("/tmp/input/"+i)
            _df = _df.select([pl.col("base_timestamp").str.strptime(pl.Datetime("ns")).alias("timestamp"), pl.col(["signal"]).suffix(f"_{signal_size}")])
        else:
            _df = pl.read_parquet("/tmp/input/"+i)

        if "depth_imbalance_" in i:
            _df = _df.drop_nulls()

            if isinstance(df, pl.DataFrame):
                df = df.vstack(_df.select(df.columns), in_place=True)
            else:
                df = _df

            df.shrink_to_fit(in_place=True)
        else:
            [_product, signal_size, _, _dateidx_csv] = i.split("_")
            _df = _df.drop_nulls()

            signal_cols.add(f"signal_{signal_size}")
            if signal_size in labeldf:
                labeldf[signal_size] = labeldf[signal_size].vstack(_df.select(labeldf[signal_size].columns), in_place=True)
            else:
                labeldf[signal_size] = _df

            labeldf[signal_size].shrink_to_fit(in_place=True)

    keys = list(labeldf.keys())
    _labeldf = labeldf[keys[0]].lazy().join(labeldf[keys[1]].lazy(), on="timestamp").join(labeldf[keys[2]].lazy(), on="timestamp")
    _labeldf = _labeldf.select([pl.col(list(signal_cols)).cast(pl.Categorical), pl.all().exclude(list(signal_cols))]).collect()

    assert isinstance(df, pl.DataFrame)
    cols = [pl.col(["timestamp"])]
    for i in df.columns:
        col = pl.col(i)
        if "spread" in i:
            col = col.alias("spread")
        elif "ask_price" in i:
            col = col.alias("ask_price")
        elif "bid_price" in i:
            col = col.alias("bid_price")
        else:
            continue
        
        cols.append(col)
        print(col)
    df2 = _labeldf.lazy().join(df.select(cols).lazy(), on="timestamp", how="outer")
    df2 = df2.with_columns(pl.col(["ask", "bid", "spread"]).forward_fill())
    df2 = df2.with_columns(pl.col(list(signal_cols)).forward_fill().fill_null("Timeout"))
    df2 = df2.with_columns(pl.col("timestamp").shift_and_fill(1, 0).alias("time_delta").cast(pl.Datetime("ns"))-pl.col("timestamp"))
    print(df2)
    df2 = df2.sort("timestamp").with_columns(pl.col("time_delta").abs()).collect()
    print(df2)
    df2 = df2.drop_nulls().sort("timestamp").with_columns(pl.col("time_delta").cast(pl.Duration('ns')))
    print(df2.sort("time_delta"))
    return df2.filter(pl.col("time_delta").abs() < pl.duration(minutes=30))


def main():
    df = load_data()
    print(df)
    outfile = "/tmp/output/file.parquet"
    df.write_parquet(outfile, compression_level=18, compression="zstd")
    S3_CONNECT.put_object(Body=open(outfile, "rb"), Bucket="compute-assets-36607b9c2d934caa8bf7d19e0251bab6", Key=f"artifacts/depth-imbalance-spread/{KEY}.parquet")

main()