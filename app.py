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
    _theme = alt.themes.enable("dark")

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
    mo.md("""## Total Price Per Head Analysis

*Does the **total price per animal** stay relatively constant across weights? This would indicate buyers pay a fixed amount per head rather than strictly per pound.*
    """)
    return


@app.cell
def _(COLOR_SCHEME, alt, filtered_df, np, pd):
    # Calculate total price per head for ALL cattle
    head_price_df = filtered_df[(filtered_df["avg_weight"] > 0) & (filtered_df["avg_price"] > 0)].copy()
    head_price_df["total_price_per_head"] = head_price_df["avg_price"] * head_price_df["avg_weight"] / 100
    head_price_df["market_type"] = head_price_df["category"] + " " + head_price_df["cattle_type"]

    # Sample for plotting (all market types)
    head_sample = head_price_df.groupby("market_type", group_keys=False).apply(
        lambda x: x.sample(n=min(len(x), 300), random_state=42), include_groups=False
    )
    head_sample["market_type"] = head_price_df.loc[head_sample.index, "market_type"]

    # Calculate R² for both models by market type
    model_comparison = []
    for _mt in sorted(head_price_df["market_type"].unique()):
        _sub = head_price_df[head_price_df["market_type"] == _mt]
        if len(_sub) > 20:
            _x = _sub["avg_weight"].values
            _y_cwt = _sub["avg_price"].values
            _y_total = _sub["total_price_per_head"].values

            # R² for $/cwt linear model
            _slope_cwt, _int_cwt = np.polyfit(_x, _y_cwt, 1)
            _pred_cwt = _int_cwt + _slope_cwt * _x
            _ss_res_cwt = np.sum((_y_cwt - _pred_cwt) ** 2)
            _ss_tot_cwt = np.sum((_y_cwt - np.mean(_y_cwt)) ** 2)
            _r2_cwt = 1 - _ss_res_cwt / _ss_tot_cwt if _ss_tot_cwt > 0 else 0

            # R² for total price linear model
            _slope_total, _int_total = np.polyfit(_x, _y_total, 1)
            _pred_total = _int_total + _slope_total * _x
            _ss_res_total = np.sum((_y_total - _pred_total) ** 2)
            _ss_tot_total = np.sum((_y_total - np.mean(_y_total)) ** 2)
            _r2_total = 1 - _ss_res_total / _ss_tot_total if _ss_tot_total > 0 else 0

            # Coefficient of variation (lower = more constant)
            _cv_total = np.std(_y_total) / np.mean(_y_total) * 100

            model_comparison.append({
                "market_type": _mt,
                "slope_cwt": _slope_cwt,
                "r2_cwt_model": _r2_cwt,
                "slope_total": _slope_total,
                "r2_total_model": _r2_total,
                "avg_price_per_head": np.mean(_y_total),
                "cv_price_per_head": _cv_total,
                "n": len(_sub),
            })

    model_df = pd.DataFrame(model_comparison)

    # Create trend line data for total price per head
    head_trend_data = []
    for _, _r in model_df.iterrows():
        _sub = head_price_df[head_price_df["market_type"] == _r["market_type"]]
        _x_min, _x_max = _sub["avg_weight"].min(), _sub["avg_weight"].max()
        for _x in np.linspace(_x_min, _x_max, 50):
            # Use the slope and intercept from the model
            _y = _r["slope_total"] * _x + (_r["avg_price_per_head"] - _r["slope_total"] * _sub["avg_weight"].mean())
            head_trend_data.append({
                "market_type": _r["market_type"],
                "avg_weight": _x,
                "total_price_per_head": _y,
            })
    head_trend_df = pd.DataFrame(head_trend_data)

    # Scatter plot: Weight vs Total Price Per Head (all market types)
    head_scatter = (
        alt.Chart(head_sample)
        .mark_circle(opacity=0.4)
        .encode(
            x=alt.X("avg_weight:Q", title="Weight (lbs)"),
            y=alt.Y("total_price_per_head:Q", title="Total Price Per Head ($)"),
            color=alt.Color("market_type:N", title="Market Type", scale=alt.Scale(range=COLOR_SCHEME)),
            tooltip=[
                "market_type",
                alt.Tooltip("avg_weight:Q", format=".0f", title="Weight"),
                alt.Tooltip("avg_price:Q", format="$.2f", title="$/cwt"),
                alt.Tooltip("total_price_per_head:Q", format="$.0f", title="Price/Head"),
            ],
        )
    )

    # Trend lines for total price per head
    head_trend_lines = (
        alt.Chart(head_trend_df)
        .mark_line(strokeWidth=3)
        .encode(
            x="avg_weight:Q",
            y="total_price_per_head:Q",
            color=alt.Color("market_type:N", scale=alt.Scale(range=COLOR_SCHEME)),
        )
    )

    head_price_chart = (
        (head_scatter + head_trend_lines)
        .properties(width="container", height=450, title="All Cattle: Weight vs Total Price Per Head")
        .interactive()
    )
    head_price_chart
    return head_price_chart, head_price_df, head_sample, head_trend_data, head_trend_df, model_comparison, model_df


@app.cell
def _(mo, model_df):
    if len(model_df) > 0:
        _analysis = """**Value of Gain Analysis by Market Type:**

The **$/Head Slope** is the market's "value of gain" - what you pay for each additional pound when buying heavier cattle.

| Market Type | N | Avg $/Head | Value of Gain ($/lb) | $/cwt Slope | Decision Guide |
|-------------|---|------------|---------------------|-------------|----------------|
"""
        for _, _r in model_df.iterrows():
            _vog = _r["slope_total"]  # Value of gain in $/lb
            _cwt_dir = "↓" if _r["slope_cwt"] < 0 else "↑"

            # Decision guide based on typical feeding costs ($1.00-$1.50/lb gain)
            if _vog < 0.80:
                _guide = "🟢 Buy heavier (cheap gain)"
            elif _vog < 1.20:
                _guide = "🟡 Near break-even"
            else:
                _guide = "🔴 Buy lighter (feed yourself)"

            _analysis += f"| {_r['market_type']} | {_r['n']:,} | ${_r['avg_price_per_head']:,.0f} | ${_vog:.2f}/lb | {_cwt_dir} {_r['slope_cwt']:.3f} | {_guide} |\n"

        _analysis += """
---
**How to use this:**
- **Value of Gain** = cost per additional pound when buying heavier cattle
- Compare to your **Cost of Gain** (feeding cost per lb, typically $0.80-$1.50/lb)
- If Value of Gain < Cost of Gain → **Buy heavier** (cheaper than feeding)
- If Value of Gain > Cost of Gain → **Buy lighter** (feed them yourself)
"""
        mo.md(_analysis)
    return


@app.cell
def _(mo):
    mo.md("### Break-Even Calculator")
    return


@app.cell
def _(mo):
    cost_of_gain_input = mo.ui.slider(start=0.50, stop=2.00, value=1.00, step=0.10, label="Your Cost of Gain ($/lb)")
    cost_of_gain_input
    return (cost_of_gain_input,)


@app.cell
def _(cost_of_gain_input, mo, model_df):
    if len(model_df) > 0:
        _cog = cost_of_gain_input.value
        _analysis = f"""**At your Cost of Gain: ${_cog:.2f}/lb**

| Market Type | Value of Gain | vs Your Cost | Recommendation |
|-------------|---------------|--------------|----------------|
"""
        for _, _r in model_df.iterrows():
            if "FEEDER" not in _r["market_type"]:
                continue
            _vog = _r["slope_total"]
            _diff = _vog - _cog

            if _diff < -0.20:
                _rec = f"✅ Buy heavier - save ${abs(_diff):.2f}/lb"
            elif _diff > 0.20:
                _rec = f"⚠️ Buy lighter - you gain ${_diff:.2f}/lb by feeding"
            else:
                _rec = "➖ Near break-even - weight doesn't matter much"

            _analysis += f"| {_r['market_type']} | ${_vog:.2f}/lb | ${_diff:+.2f}/lb | {_rec} |\n"

        _analysis += f"""
---
**Example for FEEDER STEER** (if Value of Gain = $0.80/lb):
- Buy 400 lb calf → feed to 700 lb → 300 lbs gain × ${_cog:.2f} = ${300*_cog:.0f} feed cost
- Buy 550 lb calf → feed to 700 lb → 150 lbs gain × ${_cog:.2f} = ${150*_cog:.0f} feed cost
- Difference: ${300*_cog - 150*_cog:.0f} saved on feed vs. ${150*0.80:.0f} more paid for heavier calf
"""
        mo.md(_analysis)
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
