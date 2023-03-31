import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sb
import os
import pathlib
import subprocess

DATA_DIRECTORY = pathlib.Path("/tmp/input/")

MOST_ACTIVE_PRODUCTS=["NK225", "NK225M", "JGBL", "TOPIX", "TOPIXM"]
COLS = [
    "time_passed_since_last_event_max",
    "time_passed_since_last_event_min",
    "existed_for",
    "modify_count",
    "fully_executed",
    "order_book_id"
]
def load_data(date_idx):
    """
    return order_df, product_info_df
    """
    df1 = pl.read_csv(DATA_DIRECTORY.joinpath(f"order_classification_{date_idx}.csv")).select(COLS)
    df2 = pl.read_csv(DATA_DIRECTORY.joinpath(f"product_info_{date_idx}.csv"), infer_schema_length=500000)
    return df1, df2


SAVE_FIGURE = True


def save_fig(g, filename):
    print(os.listdir("/tmp/output"))
    if SAVE_FIGURE:
        g.figure.savefig(f"/tmp/output/{filename}.jpg")
        plt.clf()
    else:
        pass


def _create_pretty_scatterplot(_df: pl.DataFrame, marker="x"):
    range_zero2hundred = range(1, 100)
    linewidth = 1
    linestyle = ":"
    line_max = 2
    percentile = _df.select("time_passed_since_last_event_max").drop_nulls().sort(
        by="time_passed_since_last_event_max").to_numpy().transpose()[0]
    percentile = np.percentile(percentile, range_zero2hundred)
    color = "orange"
    ax, _tbl_df = _main(fully_executed, max_time_between, percentile, ax=None, color=color, marker=marker,
                        use_df=_df.select(["time_passed_since_last_event_max", "fully_executed"]).drop_nulls())
    ax.set_xscale(value="log")

    plt.axvline(percentile[0], 0, line_max,
                linewidth=linewidth, linestyle=linestyle, color=color)
    plt.axvline(percentile[len(percentile)-1], 0, line_max,
                linewidth=linewidth, linestyle=linestyle, color=color)

    color = "green"
    percentile = _df.select("time_passed_since_last_event_min").drop_nulls().sort(
        by="time_passed_since_last_event_min").to_numpy().transpose()[0]
    percentile = np.percentile(percentile, range_zero2hundred)
    ax, _tbl_df = _main(fully_executed, min_time_between, percentile, ax, color=color,
                        marker=marker, use_df=_df.select(["time_passed_since_last_event_min", "fully_executed"]).drop_nulls())
    plt.axvline(percentile[0], 0, line_max,
                linewidth=linewidth, linestyle=linestyle, color=color)
    plt.axvline(percentile[len(percentile)-1], 0, line_max,
                linewidth=linewidth, linestyle=linestyle, color=color)

    percentile = _df.filter(pl.col("modify_count") == 0).select(
        "existed_for").drop_nulls().sort(by="existed_for").to_numpy().transpose()[0]
    percentile = np.percentile(percentile, range_zero2hundred)
    color = "blue"
    ax, _tbl_df = _main(fully_executed, existed_for, percentile,
                        ax, color=color, marker=marker, use_df=_df)
    plt.axvline(percentile[0], 0, line_max,
                linewidth=linewidth, linestyle=linestyle, color=color)
    plt.axvline(percentile[len(percentile)-1], 0, line_max,
                linewidth=linewidth, linestyle=linestyle, color=color)

    percentile = _df.filter(pl.col("modify_count") > 0).select(
        "existed_for").drop_nulls().sort(by="existed_for").to_numpy().transpose()[0]
    percentile = np.percentile(percentile, range_zero2hundred)
    color = "red"
    ax, _tbl_df = _main(fully_executed, existed_for, percentile,
                        ax, color=color, marker=marker, use_df=_df)
    plt.axvline(percentile[0], 0, line_max,
                linewidth=linewidth, linestyle=linestyle, color=color)
    plt.axvline(percentile[len(percentile)-1], 0, line_max,
                linewidth=linewidth, linestyle=linestyle, color=color)

    return ax


def _main(func, func2, percentile, ax=None, color=None, marker="x", use_df=None):
    stack = []
    table = []
    assert isinstance(use_df, pl.DataFrame)
    _df_dn = use_df

    _df: pl.DataFrame = func(_df_dn)
    _df2 = _df_dn
    last_val = 0
    for idx, val in enumerate(percentile):
        count1 = len(_df.filter(func2(last_val, val)))
        count2 = len(_df2.filter(func2(last_val, val)))

        prob = 0
        if count1 != 0:
            prob = count1/count2

        table.append({
            "count": count1,
            "count_full": count2,
            "rate": prob,
            "start": last_val,
            "end": val,
        })
        last_val = val
        stack.append(prob)

    _df = pl.DataFrame(table)
    g = sb.scatterplot(_df.to_pandas(), x="end", y="rate",
                       marker=marker, ax=ax, color=color)
    g.set(xlabel="nano seconds", ylabel="rate of `fully_executed` orders")
    return g, _df


def fully_executed(_df_dn):
    return _df_dn.filter(pl.col("fully_executed"))

def modfiy_count_val(val, val2):
    return pl.col("modify_count").is_between(val, val2, "right")


def max_time_between(val, val2):
    return pl.col("time_passed_since_last_event_max").is_between(val, val2, "right")


def min_time_between(val, val2):
    return pl.col("time_passed_since_last_event_min").is_between(val, val2, "right")

def existed_for(val, val2):
    return pl.col("existed_for").is_between(val, val2, "right")


def plot_future_nk225_nk225m(product_info_df: pl.DataFrame, order_classification_df: pl.DataFrame):
    _nk225_future = product_info_df.filter(pl.col("product_family").is_in(["NK225", "NK225M"])).filter(
        pl.col("product_info_financial_product") == "Future").select("product_info_order_book_id").to_series()
    order_records = order_classification_df.filter(
        pl.col("order_book_id").is_in(_nk225_future))
    ax = _create_pretty_scatterplot(order_records)
    ax.set_title("Execution rate for NK225 and NK225M futures")
    save_fig(ax, "plot_nk225_nk225m")

def plot_futures(product_info_df: pl.DataFrame, order_classification_df: pl.DataFrame):
    _future_ids = product_info_df.filter(pl.col("product_info_financial_product") == "Future").select(
        "product_info_order_book_id").to_series()
    ax = _create_pretty_scatterplot(order_classification_df.filter(
        pl.col("order_book_id").is_in(_future_ids)))
    ax.set_title("Execution rate for all future products")
    save_fig(ax, "all_future")


def plot_options(product_info_df: pl.DataFrame, order_classification_df: pl.DataFrame):
    _future_ids = product_info_df.filter(pl.col("product_info_financial_product") == "Option").select(
        "product_info_order_book_id").to_series()
    ax = _create_pretty_scatterplot(order_classification_df.filter(
        pl.col("order_book_id").is_in(_future_ids)))
    ax.set_title("Execution rate for all option products")
    save_fig(ax, "all_future")


def plot_near_expiration_target_products():
    order_df = None
    for product in MOST_ACTIVE_PRODUCTS:
        for i in range(0, 23):
            _order_df, _product_info_df = load_data(i)
            records = _product_info_df.filter(pl.col("product_info_financial_product") == "Future").filter(pl.col("product_family")==product).sort("product_info_expiration_date").select("product_info_order_book_id").to_dicts()
            id = records[0]["product_info_order_book_id"]
            if isinstance(order_df, pl.DataFrame):
                order_df = order_df.vstack(_order_df.filter(pl.col("order_book_id") == id).select(order_df.columns))
            else:
                order_df = _order_df.filter(pl.col("order_book_id") == id)
        
        assert isinstance(order_df, pl.DataFrame)
        ax = _create_pretty_scatterplot(order_df)
        ax.set_title(f"Execution rate for {product}")
        save_fig(ax, f"most_active_products_{product}")



def main():
    order_df, product_info_df = None, None
    print(os.curdir)
    print(os.listdir("."))
    try:
        os.mkdir("/tmp/output")
    except:
        pass

    subprocess.run(["bash","./download-all.sh"])

    plot = os.environ["PLOT"]

    if "plot_near_expiration_target_products" == plot:
        plot_near_expiration_target_products()
    else:
        for i in range(0, 23):
            _order_df, _product_info_df = load_data(i)
            if isinstance(order_df, pl.DataFrame) and isinstance(product_info_df, pl.DataFrame):
                productinfo_projection = set(product_info_df.columns).intersection(set(_product_info_df.columns))
                order_projection = set(_order_df.columns).intersection(set(order_df.columns))
                order_df, product_info_df = order_df.select(order_projection).vstack(_order_df.select(order_projection)), product_info_df.select(productinfo_projection).vstack(_product_info_df.select(productinfo_projection))
            else:
                order_df, product_info_df = _order_df, _product_info_df

            order_df.shrink_to_fit(True)
            product_info_df.shrink_to_fit(True)

        assert isinstance(order_df, pl.DataFrame)
        assert isinstance(product_info_df, pl.DataFrame)
        
        
        if "plot_future_nk225_nk225m" == plot:
            plot_future_nk225_nk225m(product_info_df, order_df)
        elif "plot_futures" == plot:
            plot_futures(product_info_df, order_df)
        elif "plot_options" == plot:
            plot_options(product_info_df, order_df)
        else:
            raise ""
        
    subprocess.run(["bash","./upload-all.sh"])


main()