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
import keras.callbacks
import polars as pl
import os
import json

os.environ['CUDA_VISIBLE_DEVICES'] = "0"

tf.random.set_seed(42)
os.mkdir("/tmp/input")
os.mkdir("/tmp/input/data")
os.mkdir("/tmp/input/label")
os.mkdir("/tmp/output")
SIDE = os.environ["SIDE"]
TARGET_PRODUCT = os.environ["TARGET_PRODUCT"]
DATA_FORMAT = os.environ["DATA_FORMAT"].split(";")
BUCKET = "compute-assets-36607b9c2d934caa8bf7d19e0251bab6"
S3_CLIENT = boto3.client("s3")
LABEL_SIZE = os.environ["LABEL_SIZE"]
if "EPOCS" in os.environ:
    EPOCHS = int(os.environ["EPOCS"])
else:
    EPOCHS = 1

PARAMETERS = {
    "EPOCHS": EPOCHS,
    "LABEL_SIZE": LABEL_SIZE,
    "TARGET_PRODUCT": TARGET_PRODUCT,
    "SIDE": SIDE,
    "DATA_FORMAT": DATA_FORMAT
}


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
    model.fit
    """
    model.fit(
        X[tr], [X[tr], y[tr], y[tr]], validation_data = (X[te], [X[te], y[te], y[te]]), 
                            sample_weight = sw[tr], 
                            epochs = 100, batch_size = batch_size, callbacks = [ckp, es], verbose = 0
    )
    """
    return model

# %%


def prepare_model(width: int):
    params = {
        'num_columns': width,
        'num_labels': 1,
        'hidden_units': [96, 96, 896, 448, 448, 256],
        'dropout_rates': [0.03527936123679956, 0.038424974585075086, 0.42409238408801436, 0.10431484318345882, 0.49230389137187497, 0.32024444956111164, 0.2716856145683449, 0.4379233941604448],
        'ls': 0,
        'lr': 1e-3,
    }

    model = create_ae_mlp(**params)
    return model


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


def file_to_disk(key: str, body, date_idx, is_data=False):
    path = pathlib.Path(key)
    filename = path.name.replace(".csv.zst", ".csv")
    try:
        os.mkdir(f"/tmp/input/data/{date_idx}/")
    except:
        pass

    if is_data:
        filepath = f"/tmp/input/data/{date_idx}/{filename}"
    else:
        filepath = f"/tmp/input/label/{date_idx}.csv"
    fp = open(filepath, "wb")
    if key.endswith("zst"):
        s = zstd.decompress(body.read())
    else:
        s = body.read()
    fp.write(s)
    fp.flush()
    fp.close()


def download_files():
    print("starting download", flush=True)
    df = pl.read_parquet("./files.parquet")
    df = df.filter(pl.col("data_format").is_in(DATA_FORMAT))
    df = df.filter(pl.col("product") == TARGET_PRODUCT.upper())
    for i in df.to_dicts():
        print("downloading: ", i["key"], flush=True)
        obj = S3_CLIENT.get_object(Bucket=BUCKET, Key=i["key"])
        file_to_disk(i["key"], obj["Body"], i["dateidx"], is_data=True)

    label_df = pl.read_parquet("./labels.parquet")
    for i in label_df.filter(pl.col("product") == TARGET_PRODUCT.lower()).filter(pl.col("label_size") == LABEL_SIZE).to_dicts():
        print("downloading: ", i["key"], flush=True)
        obj = S3_CLIENT.get_object(Bucket=BUCKET, Key=i["key"])
        file_to_disk(i["key"], obj["Body"], i["dateidx"])


def filename_to_format(name: str):
    if "order_depth" in name:
        return "order_depth"
    elif "depth_imbalance" in name:
        return "depth_imbalance"
    elif "taker" in name:
        return "taker_positions"
    else:
        raise BaseException(name)


def feature_engineering(df: pl.DataFrame):
    window = [
        "1s"
        "1m",
        "15m"
        "60m",
        "120m"
    ]
    df2 = None
    df = df.sort("timestamp")
    for period in window:
        df3 = df.groupby_rolling(index_column="timestamp", period=period, closed="right").agg(
            [
                pl.col(pl.Float32).mean().map_alias(lambda x: x+"_mean"),
                pl.col(pl.Float32).max().map_alias(lambda x: x+"_max"),
                pl.col(pl.Float32).min().map_alias(lambda x: x+"_min"),
                pl.col(pl.Float32).std().map_alias(lambda x: x+"_std"),
            ]
        )

        if isinstance(df2, pl.DataFrame):
            df3 = df3.join(df2, on="timestamp")
        else:
            df2 = df3

    assert isinstance(df2, pl.DataFrame)
    return df2.sort("timestamp").select([pl.col("timestamp"), pl.col(pl.Float32).pct_change().fill_null(0.).fill_nan(0.)])


def dataiter(range_start: int, range_end: int):
    for idx in range(range_start, range_end):
        stack: list[pl.DataFrame] = []
        for i in pathlib.Path(f"/tmp/input/data/{idx}").iterdir():
            lf = load_data(DATA_FORMAT, i)
            N = [pl.Int64, pl.Float64, pl.Float32, pl.Int32, pl.Int16]
            df = lf.select(
                [pl.col("timestamp"), pl.col(N).cast(pl.Float32)]).collect()
            stack.append(df)

        df_X = stack[0]
        for df2 in stack[1:]:
            df_X = df_X.join(df2, on="timestamp",
                             how="outer").sort("timestamp")

        df_X = df_X.sort("timestamp").fill_null(strategy="forward")
        df_Y = load_label(f"/tmp/input/label/{idx}.csv")
        df_Y = df_Y.groupby(pl.col("timestamp").dt.truncate(
            "10s")).agg([pl.col("signal").last()]).collect()

        df_Y = df_Y.join(df_X.select("timestamp"), on="timestamp", how="outer")

        df_Y = df_Y.fill_null(strategy="forward").fill_null(
            "Timeout").sort("timestamp").select(["signal", "timestamp"])

        df_X = df_X.lazy().join(df_Y.lazy().select("timestamp"), on="timestamp",
                                how="outer").sort("timestamp").fill_null(strategy="forward").fill_null(0.).collect()
        df_X = df_X.select(
            [pl.col("timestamp"), pl.col(pl.Float32)]).sort("timestamp")
        yield feature_engineering(df_X).sort("timestamp"), df_Y.fill_null("Timeout")


def df_ready_up(range_start: int, range_end: int):
    df_tup = (None, None)
    for tup in dataiter(range_start, range_end):
        if isinstance(df_tup[0], pl.DataFrame) and isinstance(df_tup[1], pl.DataFrame):
            df_tup = (df_tup[0].vstack(tup[0].select(df_tup[0].columns), in_place=True), df_tup[1].vstack(
                tup[1].select(df_tup[1].columns), in_place=True))
        else:
            df_tup = tup
    assert isinstance(df_tup[0], pl.DataFrame) and isinstance(
        df_tup[1], pl.DataFrame)
    return df_tup[0].sort("timestamp").select(pl.col(pl.Float32).fill_nan(0.).fill_null(0.)).with_columns([pl.when(pl.col(pl.Float32).is_infinite()).then(0.).otherwise(pl.col(pl.Float32)).keep_name()]), df_tup[1].sort("timestamp")


outcome = {}

def dataiter_slice(df_X: pl.DataFrame, df_Y: pl.DataFrame):
    prev = 0
    for idx in range(0, df_X.height, 5000):
        if prev != idx:
            df_X_slice = df_X[prev:idx].select(pl.col(pl.Float32))
            df_Y_slice = df_Y[prev:idx]
            yield df_X_slice, df_Y_slice
        prev = idx

    yield df_X_slice.to_pandas(), df_Y_slice.to_pandas()
def main():
    download_files()

    def train_evaluate(side):
        DATA_FORMAT_concat = "--".join(DATA_FORMAT)
        modelname = f"{DATA_FORMAT_concat}_{side}_{TARGET_PRODUCT}_{LABEL_SIZE}"
        train = df_ready_up(0, 13)
        df_X = train[0].select(pl.col(pl.Float32))
        df_Y = train[1].select(pl.col("signal") == side)

        es = EarlyStopping(monitor='val_action_AUC', min_delta=1e-4, patience=10,
                           mode='max', baseline=None, restore_best_weights=True, verbose=0)
        print("X: all data loaded onto the memory: ",
              df_X.shape, df_X.estimated_size(), flush=True)
        print("Y: all data loaded onto the memory: ",
              df_Y.shape, df_Y.estimated_size(), flush=True)
        print(df_X.describe())
        model = prepare_model(df_X.width)
        history = model.fit(dataiter_slice(df_X, df_Y), batch_size=256, validation_batch_size=256, epochs=EPOCHS, callbacks=[es])  # type: ignore
        print(history)
        test = df_ready_up(13, 23)
        df_testX = test[0]
        df_testY = test[1].select(pl.col("signal") == side)
        X, Y = df_testX.to_pandas(), df_testY.to_pandas()
        predictions = model.predict(X, batch_size=256)
        evaluation = model.evaluate(X, Y)
        side = side.lower()
        model.save(f"/tmp/output/{modelname}")

        print(history.history)
        print(predictions)
        print(evaluation)
        save_outcome(modelname, history.history, predictions,
                     evaluation, test[1].to_dicts())

    train_evaluate(SIDE)


def save_outcome(modename, history, predictions, evaluation, signal):
    key = f"model/{modename}"
    hashmap = {
        "history": history,
        "evaluation": evaluation,
        "parameters": PARAMETERS
    }
    pl.DataFrame({
        "pred": predictions[2].tranpose(),
        "signal": signal,
    }).groupby(["pred", "signal"]).count().write_parquet("./conf_matrix.parquet")

    jsondata = json.dumps(hashmap, cls=NumpyArrayEncoder)
    fp = open("meta.json", "w")
    fp.write(jsondata)
    fp.flush()
    fp.close()
    S3_CLIENT.upload_fileobj(open("meta.json", "rb"),
                             Bucket=BUCKET, Key=f"{key}/meta.json")
    S3_CLIENT.upload_fileobj(open("meta.json", "rb"),
                             Bucket=BUCKET, Key=f"{key}/conf_matrix.parquet")


class NumpyArrayEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NumpyArrayEncoder, self).default(obj)


print("starting")
main()


os.environ
# %%
