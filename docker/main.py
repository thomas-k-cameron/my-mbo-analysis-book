# %% [markdown]
# Inspired by the notebook on jane street competition

# %%
import os
from tensorflow.keras.callbacks import Callback, ReduceLROnPlateau, ModelCheckpoint, EarlyStopping
import tensorflow.keras.layers as layers
import tensorflow.keras.backend as K
import tensorflow as tf
import polars as pl
import numpy as np
import pandas as pd
import warnings
import pathlib
warnings.filterwarnings('ignore')

tf.random.set_seed(42)


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

    return model

# %%

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
        return create_ae_mlp(**params)


def load_data(format, data_path):
    if format == "taker_positions":
        lazy_frame = pl.scan_csv(data_path).with_columns(pl.col("timestamp").str.strptime(
            pl.Datetime("ns"))).drop(["status", "order_book_id"]).sort("timestamp")
    elif format == "order_depth":
        lazy_frame = pl.scan_parquet(data_path).with_columns(pl.col("timestamp").str.strptime(
            pl.Datetime("ns"))).drop(["status", "order_book_id"]).sort("timestamp")
    elif format == "depth_imbalance":
        lazy_frame = pl.scan_parquet(data_path).drop(
            ["status", "order_book_id", "product_name"]).sort("timestamp")
    else:
        raise ""
    
    return lazy_frame.select([pl.col("timestamp"), pl.col([pl.Float64, pl.Int64]).cast(pl.Float32)]).select(["timestamp", pl.col(pl.Float32)])


def load_label(data_df, label_path):
    df_label = pl.scan_csv(label_path).select(["signal", pl.col(
        "base_timestamp").alias("timestamp").str.strptime(pl.Datetime("ns"))])
    dflabel = df_label.join_asof(data_df.select("timestamp"), on="timestamp", strategy="forward").sort(
        "timestamp").select([pl.col("signal")]).collect()
    return dflabel

def train_model(side:str, df_X, df_Y):
    if side.lower() == "buy":
        df_Y = df_Y.select(pl.col("signal") == "Buy")
    elif side.lower() == "sell":
        df_Y = df_Y.select(pl.col("signal") == "Sell")
    else:
        raise ""
    model = prepare_model(side, df_X)
    model.fit(df_X, df_Y)
    model.save(f"/tmp/output/{side}.model")

def main():
    format = os.environ["DATA_FORMAT"]
    stack = []
    for i in pathlib.Path("/tmp/input/data/").iterdir():
        stack.append(load_data(format,i))
    df = stack[0]
    for df2 in stack[1:]:
        df = df.join(df2, on="timestamp")
    df_X = df.select(pl.col(pl.Float32)).collect()
    df_Y = load_label(df_X, "/tmp/input/label.csv")
    train_model("buy", df_X, df_Y)
    

main()