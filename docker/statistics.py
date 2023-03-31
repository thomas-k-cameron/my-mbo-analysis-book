import polars as pl
import seaborn as sns
import pathlib
import json

def filename_to_format(name: str):
    if "order_depth" in name:
        return "order_depth"
    elif "depth_imbalance" in name:
        return "depth_imbalance"
    elif "taker" in name:
        return "taker_positions"
    else:
        raise BaseException(name)

def load_data(format, data_path):
    filename = pathlib.Path(data_path).name
    format = filename_to_format(filename)
    if format == "taker_positions":
        suffix = filename.split("_")[4]
        cols = list(map(lambda x: pl.col(x), json.load(
            open("./synthetic_positions.json", "r"))))
        cols.append(pl.col("timestamp"))
        lazy_frame = pl.scan_csv(data_path).with_columns(pl.col("timestamp").str.strptime(
            pl.Datetime("ns"))).drop(["include_time_range_name"]).select(cols).select([pl.col("timestamp"), pl.col("*").exclude("timestamp").map_alias(lambda x: x+"_"+suffix)])
    elif format == "order_depth":
        suffix = filename.split("_")[3]
        lazy_frame = pl.scan_parquet(data_path).with_columns(pl.col("timestamp").str.strptime(
            pl.Datetime("ns"))).drop(["order_book_id"]).select([pl.col("timestamp"), pl.col("*").exclude("timestamp").map_alias(lambda x: x+"_"+suffix)])
    elif format == "depth_imbalance":
        lazy_frame = pl.scan_parquet(data_path).drop("order_book_id")
    else:
        print("format: ", format)
        raise format

    return lazy_frame.select([pl.col("timestamp"), pl.col([pl.Float64, pl.Int64]).cast(pl.Float32)]).select(["timestamp", pl.col(pl.Float32)]).sort("timestamp")


def load_label(label_path):
    df_label = pl.scan_csv(label_path).select(["signal", pl.col("base_timestamp").alias(
        "timestamp").str.strptime(pl.Datetime("ns"))]).sort("timestamp")
    return df_label

