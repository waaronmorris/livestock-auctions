import marimo

__generated_with = "0.20.4"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    import plotly.io as pio
    from pathlib import Path

    # Professional color palette (IBM colorblind-safe)
    COLOR_SEQUENCE = ["#648FFF", "#DC267F", "#FFB000", "#FE6100", "#785EF0", "#1B9E77"]

    # Custom Plotly template (dark theme to match Marimo)
    pio.templates["livestock"] = go.layout.Template(
        layout=go.Layout(
            font=dict(family="system-ui, -apple-system, sans-serif", size=12, color="#E5E7EB"),
            title=dict(font=dict(size=16, color="#F9FAFB"), x=0, xanchor="left"),
            paper_bgcolor="#1F2937",
            plot_bgcolor="#111827",
            xaxis=dict(showgrid=True, gridcolor="#374151", showline=True, linecolor="#4B5563", tickcolor="#9CA3AF"),
            yaxis=dict(showgrid=True, gridcolor="#374151", showline=False, tickcolor="#9CA3AF"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
            colorway=COLOR_SEQUENCE,
            margin=dict(l=60, r=30, t=80, b=60),
        )
    )
    pio.templates.default = "livestock"

    return COLOR_SEQUENCE, Path, go, mo, pd, pio, px


@app.cell
def _(Path, pd):
    # Load the data
    df = pd.read_csv(Path("data/clay_county_auction_data.csv"))
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
def _(COLOR_SEQUENCE, filtered_df, go):
    monthly_avg = (
        filtered_df[filtered_df["avg_price"] > 0]
        .groupby(["year_month", "cattle_type"])
        .agg({"avg_price": "mean", "head_count": "sum"})
        .reset_index()
    )

    price_fig = go.Figure()
    for _i, _ct in enumerate(sorted(monthly_avg["cattle_type"].unique())):
        _data = monthly_avg[monthly_avg["cattle_type"] == _ct].sort_values("year_month")
        price_fig.add_trace(go.Scatter(
            x=_data["year_month"], y=_data["avg_price"],
            mode="lines+markers", name=_ct,
            line=dict(width=2.5, color=COLOR_SEQUENCE[_i % len(COLOR_SEQUENCE)]),
            marker=dict(size=5),
        ))

    price_fig.update_layout(
        title="Monthly Average Prices by Cattle Type",
        xaxis_title="Month", yaxis_title="Average Price ($/cwt)",
        yaxis_tickprefix="$", height=400, hovermode="x unified",
    )
    price_fig.update_xaxes(tickangle=-45, nticks=20)
    price_fig
    return monthly_avg, price_fig


@app.cell
def _(mo):
    mo.md("## Volume Trends")
    return


@app.cell
def _(filtered_df, px):
    volume_data = filtered_df.groupby(["year_month", "category"]).agg({"head_count": "sum"}).reset_index()

    volume_fig = px.bar(
        volume_data, x="year_month", y="head_count", color="category",
        title="Monthly Volume by Category",
        labels={"year_month": "Month", "head_count": "Head Count", "category": "Category"},
        height=350,
    )
    volume_fig.update_xaxes(tickangle=-45, nticks=20)
    volume_fig
    return volume_data, volume_fig


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
def _(COLOR_SEQUENCE, filtered_df, go, halflife_slider, pd, px):
    import numpy as np
    import statsmodels.api as sm

    scatter_full = filtered_df[(filtered_df["avg_weight"] > 0) & (filtered_df["avg_price"] > 0)].copy()
    scatter_full["market_type"] = scatter_full["category"] + " " + scatter_full["cattle_type"]

    # Recency weights
    _max_date = scatter_full["auction_date"].max()
    scatter_full["days_ago"] = (_max_date - scatter_full["auction_date"]).dt.days
    _halflife_days = halflife_slider.value * 30
    scatter_full["weight"] = np.exp(-np.log(2) * scatter_full["days_ago"] / _halflife_days)

    # Weighted regression
    reg_results = []
    trend_lines = []
    for _mt in sorted(scatter_full["market_type"].unique()):
        _sub = scatter_full[scatter_full["market_type"] == _mt]
        if len(_sub) > 10:
            _X = sm.add_constant(_sub["avg_weight"])
            _model = sm.WLS(_sub["avg_price"], _X, weights=_sub["weight"]).fit()
            _int, _slope = _model.params
            reg_results.append({"market_type": _mt, "slope": _slope, "intercept": _int, "r2": _model.rsquared, "n": len(_sub)})
            _xr = np.linspace(_sub["avg_weight"].min(), _sub["avg_weight"].max(), 50)
            trend_lines.append({"mt": _mt, "x": _xr, "y": _int + _slope * _xr})

    reg_df = pd.DataFrame(reg_results)

    # Sample for plotting
    scatter_sample = scatter_full.groupby("market_type", group_keys=False).apply(
        lambda x: x.sample(n=min(len(x), 300), random_state=42), include_groups=False
    )
    scatter_sample["market_type"] = scatter_full.loc[scatter_sample.index, "market_type"]

    scatter_fig = px.scatter(
        scatter_sample, x="avg_weight", y="avg_price", color="market_type",
        title=f"Weight vs Price ({halflife_slider.value}-month half-life)",
        labels={"avg_weight": "Weight (lbs)", "avg_price": "Price ($/cwt)", "market_type": "Market Type"},
        opacity=0.5, height=500,
    )

    for _j, _t in enumerate(trend_lines):
        scatter_fig.add_trace(go.Scatter(
            x=_t["x"], y=_t["y"], mode="lines", showlegend=False,
            line=dict(color=COLOR_SEQUENCE[_j % len(COLOR_SEQUENCE)], width=3),
        ))

    scatter_fig.update_layout(yaxis_tickprefix="$")
    scatter_fig
    return np, reg_df, reg_results, scatter_fig, scatter_full, scatter_sample, sm, trend_lines


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
def _(filtered_df, px):
    yearly_data = (
        filtered_df[filtered_df["avg_price"] > 0]
        .groupby(["year", "cattle_type"])
        .agg({"avg_price": "mean"})
        .reset_index()
    )

    yearly_fig = px.bar(
        yearly_data, x="year", y="avg_price", color="cattle_type", barmode="group",
        title="Average Prices by Year and Cattle Type",
        labels={"year": "Year", "avg_price": "Avg Price ($/cwt)", "cattle_type": "Cattle Type"},
        height=400,
    )
    yearly_fig.update_layout(yaxis_tickprefix="$", xaxis_type="category")
    yearly_fig
    return yearly_data, yearly_fig


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
