import marimo

__generated_with = "0.20.4"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import numpy as np

    # Professional color palette (IBM colorblind-safe)
    COLOR_SCHEME = ["#648FFF", "#DC267F", "#FFB000", "#FE6100", "#785EF0", "#1B9E77"]

    # Configure Altair for dark theme
    alt.themes.enable("dark")

    return COLOR_SCHEME, alt, mo, np, pd


@app.cell
def _(pd):
    # Load the data from GitHub raw URL (for WASM compatibility)
    DATA_URL = "https://raw.githubusercontent.com/waaronmorris/livestock-auctions/master/data/clay_county_auction_data.csv"
    df = pd.read_csv(DATA_URL)
    df["auction_date"] = pd.to_datetime(df["auction_date"])
    df["year"] = df["auction_date"].dt.year
    df["month"] = df["auction_date"].dt.month
    df["year_month"] = df["auction_date"].dt.to_period("M").astype(str)
    df = df.fillna(0)

    # Key metrics
    latest_date = df["auction_date"].max()
    earliest_date = df["auction_date"].min()
    total_records = len(df)
    total_auctions = df["auction_date"].nunique()
    total_head = int(df["head_count"].sum())

    # Recent average price (last 6 months)
    six_months_ago = latest_date - pd.Timedelta(days=180)
    recent_df = df[df["auction_date"] >= six_months_ago]
    recent_avg_price = recent_df[recent_df["avg_price"] > 0]["avg_price"].mean()

    return df, earliest_date, latest_date, recent_avg_price, total_auctions, total_head, total_records


@app.cell
def _(earliest_date, latest_date, mo):
    mo.md(f"""
    # Clay County Livestock Auction

    **Market Analysis Dashboard** · Lineville, Alabama · {earliest_date.strftime('%b %Y')} – {latest_date.strftime('%b %Y')}
    """)
    return


@app.cell
def _(mo, recent_avg_price, total_auctions, total_head, total_records):
    mo.md(f"""
    | Total Records | Auction Days | Total Head Sold | Avg Price (6mo) |
    |:-------------:|:------------:|:---------------:|:---------------:|
    | **{total_records:,}** | **{total_auctions:,}** | **{total_head:,}** | **${recent_avg_price:.2f}/cwt** |
    """)
    return


@app.cell
def _(df, mo):
    categories = ["All"] + sorted(df["category"].unique().tolist())
    cattle_types = ["All"] + sorted(df["cattle_type"].unique().tolist())
    years = ["All"] + sorted([str(int(y)) for y in df["year"].unique().tolist()])

    category_select = mo.ui.dropdown(options=categories, value="All", label="Category")
    cattle_type_select = mo.ui.dropdown(options=cattle_types, value="All", label="Cattle Type")
    year_select = mo.ui.dropdown(options=years, value="All", label="Year")
    return categories, category_select, cattle_type_select, cattle_types, year_select, years


@app.cell
def _(category_select, cattle_type_select, mo, year_select):
    mo.hstack([category_select, cattle_type_select, year_select], justify="start", gap=1)
    return


@app.cell
def _(category_select, cattle_type_select, df, year_select):
    filtered_df = df.copy()
    if category_select.value != "All":
        filtered_df = filtered_df[filtered_df["category"] == category_select.value]
    if cattle_type_select.value != "All":
        filtered_df = filtered_df[filtered_df["cattle_type"] == cattle_type_select.value]
    if year_select.value != "All":
        filtered_df = filtered_df[filtered_df["year"] == int(year_select.value)]
    return (filtered_df,)


@app.cell
def _(filtered_df, mo):
    mo.md(f"*Showing {len(filtered_df):,} records*")
    return


@app.cell
def _(mo):
    mo.md("## Price Trends Over Time")
    return


@app.cell
def _(COLOR_SCHEME, alt, filtered_df):
    monthly_avg = (
        filtered_df[filtered_df["avg_price"] > 0]
        .groupby(["year_month", "cattle_type"])
        .agg({"avg_price": "mean", "head_count": "sum"})
        .reset_index()
    )

    price_chart = (
        alt.Chart(monthly_avg)
        .mark_line(point=True)
        .encode(
            x=alt.X("year_month:O", title="Month", axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("avg_price:Q", title="Average Price ($/cwt)"),
            color=alt.Color("cattle_type:N", title="Cattle Type", scale=alt.Scale(range=COLOR_SCHEME)),
            tooltip=["year_month", "cattle_type", alt.Tooltip("avg_price:Q", format="$.2f"), "head_count:Q"],
        )
        .properties(width="container", height=400, title="Monthly Average Prices by Cattle Type")
        .interactive()
    )
    price_chart
    return monthly_avg, price_chart


@app.cell
def _(mo):
    mo.md("## Volume Trends")
    return


@app.cell
def _(COLOR_SCHEME, alt, filtered_df):
    volume_data = filtered_df.groupby(["year_month", "category"]).agg({"head_count": "sum"}).reset_index()

    volume_chart = (
        alt.Chart(volume_data)
        .mark_bar()
        .encode(
            x=alt.X("year_month:O", title="Month", axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("head_count:Q", title="Head Count"),
            color=alt.Color("category:N", title="Category", scale=alt.Scale(range=COLOR_SCHEME)),
            tooltip=["year_month", "category", "head_count:Q"],
        )
        .properties(width="container", height=350, title="Monthly Volume by Category")
        .interactive()
    )
    volume_chart
    return volume_chart, volume_data


@app.cell
def _(mo):
    mo.md("## Weight vs Price Analysis")
    return


@app.cell
def _(mo):
    halflife_slider = mo.ui.slider(start=6, stop=60, value=24, step=6, label="Recency half-life (months)")
    halflife_slider
    return (halflife_slider,)


@app.cell
def _(COLOR_SCHEME, alt, filtered_df, halflife_slider, np, pd):
    scatter_full = filtered_df[(filtered_df["avg_weight"] > 0) & (filtered_df["avg_price"] > 0)].copy()
    scatter_full["market_type"] = scatter_full["category"] + " " + scatter_full["cattle_type"]

    # Recency weights
    _max_date = scatter_full["auction_date"].max()
    scatter_full["days_ago"] = (_max_date - scatter_full["auction_date"]).dt.days
    _halflife_days = halflife_slider.value * 30
    scatter_full["weight"] = np.exp(-np.log(2) * scatter_full["days_ago"] / _halflife_days)

    # Simple weighted regression using numpy (no statsmodels needed)
    reg_results = []
    for _mt in sorted(scatter_full["market_type"].unique()):
        _sub = scatter_full[scatter_full["market_type"] == _mt]
        if len(_sub) > 10:
            # Weighted least squares using numpy
            _x = _sub["avg_weight"].values
            _y = _sub["avg_price"].values
            _w = _sub["weight"].values

            # Weighted mean
            _xw = np.sum(_w * _x) / np.sum(_w)
            _yw = np.sum(_w * _y) / np.sum(_w)

            # Weighted slope and intercept
            _num = np.sum(_w * (_x - _xw) * (_y - _yw))
            _den = np.sum(_w * (_x - _xw) ** 2)
            _slope = _num / _den if _den != 0 else 0
            _intercept = _yw - _slope * _xw

            # R-squared
            _y_pred = _intercept + _slope * _x
            _ss_res = np.sum(_w * (_y - _y_pred) ** 2)
            _ss_tot = np.sum(_w * (_y - _yw) ** 2)
            _r2 = 1 - _ss_res / _ss_tot if _ss_tot != 0 else 0

            reg_results.append({
                "market_type": _mt,
                "slope": _slope,
                "intercept": _intercept,
                "r2": _r2,
                "n": len(_sub),
                "x_min": _sub["avg_weight"].min(),
                "x_max": _sub["avg_weight"].max(),
            })

    reg_df = pd.DataFrame(reg_results)

    # Sample for plotting (max 300 per market type)
    scatter_sample = scatter_full.groupby("market_type", group_keys=False).apply(
        lambda x: x.sample(n=min(len(x), 300), random_state=42), include_groups=False
    )
    scatter_sample["market_type"] = scatter_full.loc[scatter_sample.index, "market_type"]

    # Create trend line data
    trend_data = []
    for _, _r in reg_df.iterrows():
        for _x in np.linspace(_r["x_min"], _r["x_max"], 50):
            trend_data.append({
                "market_type": _r["market_type"],
                "avg_weight": _x,
                "avg_price": _r["intercept"] + _r["slope"] * _x,
            })
    trend_df = pd.DataFrame(trend_data)

    # Scatter plot
    scatter_points = (
        alt.Chart(scatter_sample)
        .mark_circle(opacity=0.5)
        .encode(
            x=alt.X("avg_weight:Q", title="Weight (lbs)"),
            y=alt.Y("avg_price:Q", title="Price ($/cwt)"),
            color=alt.Color("market_type:N", title="Market Type", scale=alt.Scale(range=COLOR_SCHEME)),
            tooltip=["market_type", alt.Tooltip("avg_weight:Q", format=".0f"), alt.Tooltip("avg_price:Q", format="$.2f")],
        )
    )

    # Trend lines
    trend_lines = (
        alt.Chart(trend_df)
        .mark_line(strokeWidth=3)
        .encode(
            x="avg_weight:Q",
            y="avg_price:Q",
            color=alt.Color("market_type:N", scale=alt.Scale(range=COLOR_SCHEME)),
        )
    )

    scatter_chart = (
        (scatter_points + trend_lines)
        .properties(width="container", height=500, title=f"Weight vs Price ({halflife_slider.value}-month half-life)")
        .interactive()
    )
    scatter_chart
    return reg_df, reg_results, scatter_chart, scatter_full, scatter_sample, trend_data, trend_df, trend_lines, scatter_points


@app.cell
def _(halflife_slider, mo, reg_df):
    if len(reg_df) > 0:
        _rows = "| Market Type | Equation | R² | N | Trend |\n|---|---|---|---|---|\n"
        for _, _r in reg_df.iterrows():
            _dir = "↓" if _r["slope"] < 0 else "↑"
            _rows += f"| {_r['market_type']} | y = {_r['slope']:.4f}x + {_r['intercept']:.1f} | {_r['r2']:.3f} | {_r['n']:,} | {_dir} |\n"
        mo.md(f"**Regression Equations ({halflife_slider.value}-month half-life)**\n\n{_rows}")
    return


@app.cell
def _(mo):
    mo.md("## Year-over-Year Comparison")
    return


@app.cell
def _(COLOR_SCHEME, alt, filtered_df):
    yearly_data = (
        filtered_df[filtered_df["avg_price"] > 0]
        .groupby(["year", "cattle_type"])
        .agg({"avg_price": "mean"})
        .reset_index()
    )

    yearly_chart = (
        alt.Chart(yearly_data)
        .mark_bar()
        .encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y("avg_price:Q", title="Avg Price ($/cwt)"),
            color=alt.Color("cattle_type:N", title="Cattle Type", scale=alt.Scale(range=COLOR_SCHEME)),
            xOffset="cattle_type:N",
            tooltip=["year", "cattle_type", alt.Tooltip("avg_price:Q", format="$.2f")],
        )
        .properties(width="container", height=400, title="Average Prices by Year and Cattle Type")
    )
    yearly_chart
    return yearly_chart, yearly_data


@app.cell
def _(mo):
    mo.md("## Summary Statistics")
    return


@app.cell
def _(filtered_df, mo):
    summary = (
        filtered_df[filtered_df["avg_price"] > 0]
        .groupby(["category", "cattle_type"])
        .agg({"avg_price": ["mean", "min", "max"], "head_count": "sum", "avg_weight": "mean"})
        .round(2)
    )
    summary.columns = ["Avg Price", "Min Price", "Max Price", "Total Head", "Avg Weight"]
    summary = summary.reset_index()
    mo.ui.table(summary, selection=None)
    return (summary,)


@app.cell
def _(mo):
    mo.md("""
    ---
    **Data Source:** USDA Agricultural Marketing Service (AMS) · Clay County Livestock Auction, Lineville, AL
    Report ID: AMS_1989 · Updated weekly
    """)
    return


if __name__ == "__main__":
    app.run()
