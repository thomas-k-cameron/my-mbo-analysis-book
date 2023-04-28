import polars as pl
import seaborn as sns
import matplotlib.pyplot as plt
import boto3
import pathlib
import os
import sys

SIGNAL = sys.argv[1]
FILE = pathlib.Path(os.environ["FILE"])
PATH = pathlib.Path("/tmp/input/").joinpath(FILE.name)
BUCKET = "compute-assets-36607b9c2d934caa8bf7d19e0251bab6"
# download
s3conn = boto3.client("s3")
s3conn.download_file(BUCKET, os.environ["FILE"], PATH)


def main(path: pathlib.Path, hue_col, x_col_str, ax1=None, ax2=None):
    filcond = pl.col("")
    x_col = pl.col("")
    if x_col_str == "ask_price":
        x_col = pl.col(x_col_str)
        filcond = pl.col("ask_can_be_filled")
    elif x_col_str == "bid_price":
        x_col = pl.col(x_col_str)
        filcond = pl.col("bid_can_be_filled")
    elif x_col_str == "spread":
        x_col = pl.col("bid_price") - pl.col("ask_price").abs()
        filcond = pl.all([pl.col("ask_can_be_filled"),
                         pl.col("bid_can_be_filled")])

    df = pl.read_parquet(path).sort("timestamp")

    df1 = df.filter(filcond)
    td = pl.col("time_delta").cast(pl.UInt64)
    cols = [x_col.alias(x_col_str), td, pl.col(hue_col).cast(pl.Utf8)]
    df = df1.select(cols)

    print(x_col, df.shape)

    labels = ["Buy", "Sell", "Timeout"]
    g = sns.histplot(
        df.to_pandas(),
        weights="time_delta",
        x=x_col_str,
        hue=hue_col,
        multiple="fill",
        linewidth=.0,
        bins=100,
        ax=ax1,
        hue_order=labels
    )
    [product, qty1, qty2] = path.name.replace(".parquet", "").split("_")
    g.set_title(
        f"{product}: `Depth Imalance`({x_col_str}, {hue_col}, {qty1}, {qty2})")
    g = sns.histplot(data=df.select([x_col_str, td]).to_pandas(
    ), x=x_col_str, ax=ax2, bins=100,  weights="time_delta")
    g.set_yscale("log")
    plt.tight_layout()


def pic_file_path_func(path: pathlib.Path, signal: str):
    n = path.name.replace(".parquet", "")
    filename = "_".join([n, signal])+".png"
    return "/tmp/input/"+filename


def create_set(path, signal):
    import time
    savefig = "/tmp/output/"
    stack = []
    for i in ["ask_price", "bid_price", "spread"]:
        plt.close()
        f, ax = plt.subplots(2, 1, figsize=(7, 5), sharex=True)
        sns.despine(f)
        h, l = ax[0].get_legend_handles_labels()
        ax[0].legend(handles=h, loc="upper left",
                     bbox_to_anchor=(1, 1), labels=l)
        main(path, signal, i, ax1=ax[0], ax2=ax[1])
        filename = "_".join(
            [i, signal.replace("signal_", ""), FILE.name.replace(".parquet", ".png")])
        savepath = savefig+filename
        f.savefig(savepath)
        key = "artifacts/depth-imbalance-spread-filter-pics-2/"+filename
        stack.append((savepath, key))

    time.sleep(1)
    for i in stack:
        print(i)
        asdf = s3conn.upload_fileobj(
            open(i[0], "rb"),
            BUCKET,
            i[1]
        )
        print(asdf)
        time.sleep(1)


create_set(PATH, SIGNAL)
