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


def main(path: pathlib.Path, hue_col, x_col, ax1=None, ax2=None):
    df = pl.read_parquet(path)
    print(df)
    td = pl.col("time_delta").cast(pl.UInt64)
    labels = ["Buy", "Sell", "Timeout"]
    g = sns.histplot(
        df.select([pl.col(x_col), td, pl.col(
            hue_col).cast(pl.Utf8)]).to_pandas(),
        weights="time_delta",
        x=x_col,
        hue=hue_col,
        multiple="fill",
        linewidth=.0,
        bins=100,
        ax=ax1,
        hue_order=labels
    )
    [product, qty1, qty2] = path.name.replace(".parquet", "").split("_")
    g.set_title(f"{product}: `Depth Imalance`({qty1}, {qty2})")
    g = sns.histplot(data=df.select([x_col, td]).to_pandas(), x=x_col, ax=ax2, bins=100,  weights="time_delta")
    g.set_yscale("log")
    plt.tight_layout()


def pic_file_path_func(path: pathlib.Path, signal: str):
    n = path.name.replace(".parquet", "")
    filename = "_".join([n, signal])+".png"
    return "/tmp/input/"+filename


def create_set(path, signal):
    savefig = "/tmp/output/main.png"
    for i in ["ask", "bid", "spread"]:
        f, ax = plt.subplots(2, 1, figsize=(7, 5), sharex=True)
        sns.despine(f)
        h, l = ax[0].get_legend_handles_labels()
        ax[0].legend(handles = h, loc="upper left", bbox_to_anchor=(1, 1), labels=l)
        main(path, signal, i, ax1=ax[0], ax2=ax[1])
        f.savefig(savefig)
        key = "artifacts/depth-imbalance-spread-pics/"+"_".join([i, signal.replace("signal_", ""), FILE.name.replace(".parquet", ".png")])
        s3conn.upload_fileobj(
            open(savefig, "rb"),
            BUCKET,
            key
        )
        print(key)


create_set(PATH, SIGNAL)
