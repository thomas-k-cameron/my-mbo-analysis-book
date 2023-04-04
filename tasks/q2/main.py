# %%
import polars as pl
import os 
import boto3 

PRODUCT = os.environ["PRODUCT"]
TIME_RANGE = os.environ["TIME_RANGE"]
SIZE_THING = os.environ["SIZE_THING"]
DATA = os.environ["DATA"]
LABELS = os.environ["LABELS"]

KEY=f"{PRODUCT}_{TIME_RANGE}_{SIZE_THING}"

BUCKET_NAME="compute-assets-36607b9c2d934caa8bf7d19e0251bab6"
S3_CONNECT = boto3.client("s3")

def load_data():
    df = None
    labeldf = None
    for i in os.listdir("/tmp/input"):
        _df = pl.read_csv("/tmp/input/"+i)
        if "synthetic_taker_positions_" in i:
            _df = _df.select([pl.all().exclude("timestamp"), pl.col("timestamp").str.strptime(pl.Datetime("ns"))])
            if isinstance(df, pl.DataFrame):
                df = df.vstack(_df.select(df.columns), in_place=True)
            else:
                df = _df

            df.shrink_to_fit(in_place=True)
        else:
            _df = _df.select([pl.col("base_timestamp").str.strptime(pl.Datetime("ns")).alias("timestamp"), pl.col("signal")])
            if isinstance(labeldf, pl.DataFrame):
                labeldf = labeldf.vstack(_df.select(labeldf.columns), in_place=True)
            else:
                labeldf = _df

            labeldf.shrink_to_fit(in_place=True)
            

    assert isinstance(df, pl.DataFrame) and isinstance(labeldf, pl.DataFrame)
    print("joining")
    df = labeldf.join(df, on="timestamp", how="outer").sort("timestamp").select([pl.all().exclude("signal"), pl.col("signal").forward_fill()])
    return df

def process(df: pl.DataFrame):
    def func(i):
        stack = [pl.col(i).count().alias("count"), pl.col(i).skew().alias("skew"), pl.col(i).kurtosis().alias("kurtosis"), pl.col(i).var().alias("var"), pl.col(i).mean().alias("mean")]
        return stack

    vstackdf = None
    lower_upper = lambda i: [pl.col(i).quantile(0.01).alias("q01"), pl.col(i).quantile(0.99).alias("q99")]
    for i in df.columns:
        if i == "include_time_range_name" or i == "timestamp" or i == "signal" or i == "target_product_group":
            continue

        _df = df.drop_nulls().select([pl.col("signal"), pl.col(i).pct_change()]).filter(pl.col(i).is_not_null()).filter(pl.col(i).is_not_nan()).filter(pl.col(i).is_finite())
        dictmap = _df.select(lower_upper(i)).to_dicts()[0]
        upper_bound = dictmap["q99"]
        lower_bound = dictmap["q01"]
        print(dictmap)
        print(i)

        _df1 = _df.filter(pl.col(i).is_between(lower_bound, upper_bound, "right")).filter(pl.col(i) != 0).groupby(pl.col("signal")).agg(func(i)).sort(pl.col("signal"))
        _df2 = _df.groupby(pl.col("signal")).agg(lower_upper(i)).sort(pl.col("signal"))
        _df = _df1.join(_df2, on="signal").with_columns(pl.repeat(i, _df1.height)).sort("signal")
        print(_df, flush=True)
        if isinstance(vstackdf, pl.DataFrame):
            vstackdf = vstackdf.vstack(_df)
        else:
            vstackdf = _df

    return vstackdf

def main():
    # load data
    df = load_data()
    dfdone = process(df)
    assert isinstance(dfdone, pl.DataFrame)
    outfle = "/tmp/output/file.parquet"
    PRODUCT = os.environ["PRODUCT"]
    TIME_RANGE = os.environ["TIME_RANGE"]
    SIZE_THING = os.environ["SIZE_THING"]
    dfdone = dfdone.with_columns([
        pl.repeat(PRODUCT, dfdone.height).alias("product"),
        pl.repeat(TIME_RANGE, dfdone.height).alias("time_range"),
        pl.repeat(SIZE_THING, dfdone.height).alias("size_thing"),
    ])
    dfdone.write_parquet(outfle, compression_level=15, compression="zstd")
    S3_CONNECT.put_object(Body=open(outfle, "rb"), Bucket="compute-assets-36607b9c2d934caa8bf7d19e0251bab6", Key=f"artifacts/data-stats/{KEY}.parquet")

main()