# %% [markdown]
# Inspired by the notebook on jane street competition

# %%
import zstd
import boto3
import pathlib
import warnings
import pandas as pd
import numpy as np
import tensorflow as tf
import tensorflow.keras.backend as K
import tensorflow.keras.layers as layers
from tensorflow.keras.callbacks import Callback, ReduceLROnPlateau, ModelCheckpoint, EarlyStopping
import asyncio
import polars as pl
import sys
import subprocess
import os
import json
os.environ['CUDA_VISIBLE_DEVICES'] = "0"


tf.random.set_seed(42)
os.mkdir("/tmp/input")
os.mkdir("/tmp/input/data")
os.mkdir("/tmp/output")
TARGET_PRODUCT = os.environ["TARGET_PRODUCT"]
DATA_FORMAT = os.environ["DATA_FORMAT"]
BUCKET = "compute-assets-36607b9c2d934caa8bf7d19e0251bab6"
S3_CLIENT = boto3.client("s3")
LABEL_SIZE = os.environ["LABEL_SIZE"]


def create_ae_mlp(num_columns, num_labels, hidden_units, dropout_rates, ls=1e-2, lr=1e-3):

    inp = tf.keras.layers.Input(shape=(num_columns, ))
    x0 = tf.keras.layers.BatchNormalization()(inp)

    encoder = tf.keras.layers.GaussianNoise(dropout_rates[0])(x0)
    encoder = tf.keras.layers.Dense(hidden_units[0])(encoder)
    encoder = tf.keras.layers.BatchNormalization()(encoder)
    encoder = tf.keras.layers.Activation('swish')(encoder)

    decoder = tf.keras.layers.Dropout(dropout_rates[1])(encoder)
    decoder = tf.keras.layers.Dense(num_columns, name='decoder')(decoder)

    x_ae = tf.keras.layers.Dense(hidden_units[1])(decoder)
    x_ae = tf.keras.layers.BatchNormalization()(x_ae)
    x_ae = tf.keras.layers.Activation('swish')(x_ae)
    x_ae = tf.keras.layers.Dropout(dropout_rates[2])(x_ae)

    out_ae = tf.keras.layers.Dense(
        num_labels, activation='sigmoid', name='ae_action')(x_ae)

    x = tf.keras.layers.Concatenate()([x0, encoder])
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(dropout_rates[3])(x)

    for i in range(2, len(hidden_units)):
        x = tf.keras.layers.Dense(hidden_units[i])(x)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.Activation('swish')(x)
        x = tf.keras.layers.Dropout(dropout_rates[i + 2])(x)

    out = tf.keras.layers.Dense(
        num_labels, activation='sigmoid', name='action')(x)

    model = tf.keras.models.Model(inputs=inp, outputs=[decoder, out_ae, out])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
                  loss={'decoder': tf.keras.losses.MeanSquaredError(),
                        'ae_action': tf.keras.losses.BinaryCrossentropy(label_smoothing=ls),
                        'action': tf.keras.losses.BinaryCrossentropy(label_smoothing=ls),
                        },
                  metrics={'decoder': tf.keras.metrics.MeanAbsoluteError(name='MAE'),
                           'ae_action': tf.keras.metrics.AUC(name='AUC'),
                           'action': tf.keras.metrics.AUC(name='AUC'),
                           },
                  )
    model.evaluate
    return model

# %%


def prepare_model(side, df):
    import pathlib
    path = pathlib.Path(f"/tmp/model/{side}.model")
    params = {
        'num_columns': df.width,
        'num_labels': 1,
        'hidden_units': [96, 96, 896, 448, 448, 256],
        'dropout_rates': [0.03527936123679956, 0.038424974585075086, 0.42409238408801436, 0.10431484318345882, 0.49230389137187497, 0.32024444956111164, 0.2716856145683449, 0.4379233941604448],
        'ls': 0,
        'lr': 1e-3,
    }
    if path.is_file():
        return tf.keras.models.load_model(path)
    else:
        model = create_ae_mlp(**params)
        model.evaluate
        return model


def load_data(format, data_path):
    filename = pathlib.Path(data_path).name
    if format == "taker_positions":
        suffix = filename.split("_")[4]
        cols = list(map(lambda x: pl.col(x), json.load(
            open("./synthetic_positions.json", "r"))))
        cols.append(pl.col("timestamp"))
        lazy_frame = pl.scan_csv(data_path).with_columns(pl.col("timestamp").str.strptime(
            pl.Datetime("ns"))).drop(["include_time_range_name"]).select(cols).select([pl.col("timestamp"), pl.col("*").exclude("timestamp").map_alias(lambda x: x+"_"+suffix)])
    elif format == "order_depth":
        suffix = filename.split("_")[3]
        print('suffix: ', suffix)
        lazy_frame = pl.scan_parquet(data_path).with_columns(pl.col("timestamp").str.strptime(
            pl.Datetime("ns"))).drop(["order_book_id"]).select([pl.col("timestamp"), pl.col("*").exclude("timestamp").map_alias(lambda x: x+"_"+suffix)])
    elif format == "depth_imbalance":
        lazy_frame = pl.scan_parquet(data_path).drop("order_book_id")
    else:
        raise ""

    return lazy_frame.select([pl.col("timestamp"), pl.col([pl.Float64, pl.Int64]).cast(pl.Float32)]).select(["timestamp", pl.col(pl.Float32)]).sort("timestamp")

def feature_engineering(lazy_frame: pl.LazyFrame):
    lazy_frame.select([
        pl.col(pl.Float32).rolling_mean("60s", by="timestamp"),
        pl.col(pl.Float32).rolling_mean("15m", by="timestamp"),
        pl.col(pl.Float32).rolling_mean("60m", by="timestamp"),
    ])

def load_label(data_df: pl.DataFrame, label_path):
    df_label = pl.scan_csv(label_path).select(["signal", pl.col(
        "base_timestamp").alias("timestamp").str.strptime(pl.Datetime("ns"))]).sort("timestamp")
    dflabel = df_label.join_asof(data_df.select("timestamp").lazy(), on="timestamp", strategy="forward").sort(
        "timestamp").collect()
    return dflabel


def train_model(side: str, df_X: pl.DataFrame, df_Y: pl.DataFrame, model=None):
    if side.lower() == "buy":
        df_Y = df_Y.select(pl.col("signal") == "Buy")
    elif side.lower() == "sell":
        df_Y = df_Y.select(pl.col("signal") == "Sell")
    else:
        raise ""
    if model == None:
        model = prepare_model(side, df_X)

    prev = 0
    for i in range(0, df_X.height, 5000*8):
        if prev == i:
            continue
        df_X_slice = df_X[prev:i]
        df_Y_slice = df_Y[prev:i]
        model.fit(df_X_slice.to_pandas(), df_Y_slice.to_pandas())
        print("", flush=True)
        prev = i
    return model


def file_to_disk(key: str, filetype, body):
    filename = pathlib.Path(key).name
    if filetype == "data":
        filepath = f"/tmp/input/data/{filename}"
    else:
        filepath = "/tmp/input/label.csv"
    fp = open(filepath.replace(".csv.zst", ".csv"), "wb")
    if key.endswith("zst"):
        s = zstd.decompress(body.read())
    else:
        s = body.read()
    fp.write(s)
    fp.flush()
    fp.close()


def download_files(idx: str):
    print(os.listdir("/tmp/input/data"), flush=True)
    for i in os.listdir("/tmp/input/data"):
        os.remove(f"/tmp/input/data/{i}")
    try:
        os.remove("/tmp/input/label.csv")
    except:
        pass
    print("starting download", flush=True)
    df = pl.read_parquet("./files.parquet")
    df = df.filter(pl.col("data_format") == DATA_FORMAT)
    df = df.filter(pl.col("product") == TARGET_PRODUCT.upper())
    df = df.filter(pl.col("dateidx") == idx)
    for i in df.to_dicts():
        print("downloading: ", i["key"], flush=True)
        obj = S3_CLIENT.get_object(Bucket=BUCKET, Key=i["key"])
        file_to_disk(i["key"], "data", obj["Body"])

    label_df = pl.read_parquet("./labels.parquet")
    for i in label_df.filter(pl.col("dateidx") == idx).filter(pl.col("product") == TARGET_PRODUCT.lower()).filter(pl.col("label_size") == LABEL_SIZE).to_dicts():
        print("downloading: ", i["key"], flush=True)
        obj = S3_CLIENT.get_object(Bucket=BUCKET, Key=i["key"])
        file_to_disk(i["key"], "label", obj["Body"])


def process_files(buymodel, sellmodel):
    stack: list[pl.LazyFrame] = []
    for i in pathlib.Path("/tmp/input/data/").iterdir():
        lf = load_data(DATA_FORMAT, i)
        stack.append(lf)
    df = stack[0]
    for df2 in stack[1:]:
        df = df.join(df2, on="timestamp")
    
    df_X = df.select([pl.col("timestamp"), pl.col(pl.Float32)]).collect()
    df_Y = load_label(df_X, "/tmp/input/label.csv")
    if df_X.height != df_Y.height:
        df_X = df_X.join_asof(df_Y, on="timestamp")
    df_Y = df_Y.select("signal")
    print(df_X)
    print("all data loaded onto the memory: ",
          df_X.estimated_size(), flush=True)
    print("label loaded onto the memory: ", df_X.estimated_size(), flush=True)
    buymodel = train_model("buy", df_X, df_Y, buymodel)
    sellmodel = train_model("sell", df_X, df_Y, sellmodel)
    return buymodel, sellmodel


def main():
    buymodel, sellmodel = None, None
    for i in range(0, 13):
        download_files(str(i))
        buymodel, sellmodel = process_files(buymodel, sellmodel)
    buymodel.save("/tmp/output/buy")
    sellmodel.save("/tmp/output/sell")
    suffix = f"{DATA_FORMAT}_{TARGET_PRODUCT}/{LABEL_SIZE}"

    def upload_model(directory):
        os.system(
            f"aws s3 cp /tmp/output/{directory} s3://{BUCKET}/model/{directory}/{suffix} --recursive")
    print(os.walk(f"/tmp/output/buy"))
    upload_model("buy")
    upload_model("sell")


print("starting")
main()
