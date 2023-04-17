import os
import polars as pl
import seaborn as sns
import matplotlib.pyplot as plt

def show_plot(path: str, x, signals):
    df = pl.read_parquet(path)
    df = df.with_columns(pl.col(pl.Categorical).cast(pl.Utf8).cast(pl.Categorical))
    min, max = pl.col(x).quantile(0.001).alias("min"), pl.col(x).quantile(0.999).alias("max")
    def print_signal_depth_thing(df, signal, ax = None):
        signal = f"signal_{signal}"
        sns.kdeplot(df.select([pl.col(signal), pl.col(x)]).to_pandas(), x=x, weights=df.select(pl.col("time_delta").shift(-1))["time_delta"].to_pandas(), hue=signal, hue_order=["Buy", "Sell", "Timeout"], ax = ax, multiple="fill")

    tup = plt.subplots(3, 1, sharey=True)
    idx = 0
    tup[1][0].set_title(f"{x}: {path}")
    for i in tup[1][1:]:
        i.tick_params(axis='y', which="both", left = False, right = False)
    for i in signals:
        print_signal_depth_thing(df, i, tup[1][idx])
        idx+=1
    for i in tup[1]:
        i.legend().remove()
    tup[0].tight_layout()
    
JGBL_SIGNAL_SIZE =[150, 300, 500]
def sort_key(i: str):
    [_, n, n2] = i.replace(".parquet", "").split("_")
    return (int(n), int(n2))

path = os.environ["PATH"]
show_plot(path, "bid", JGBL_SIGNAL_SIZE)
show_plot(path, "ask", JGBL_SIGNAL_SIZE)
show_plot(path, "spread", JGBL_SIGNAL_SIZE)