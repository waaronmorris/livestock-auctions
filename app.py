import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import plotly.express as px
    from pathlib import Path

    return Path, alt, mo, pd, px


@app.cell
def _(Path, pd):
    # Load the data
    df = pd.read_csv(Path("data/clay_county_auction_data.csv"))
    df["auction_date"] = pd.to_datetime(df["auction_date"])
    df["year"] = df["auction_date"].dt.year
    df["month"] = df["auction_date"].dt.month
    df["year_month"] = df["auction_date"].dt.to_period("M").astype(str)

    # Clean data - replace NaN with None for JSON compatibility
    df = df.fillna(0)
    return (df,)


@app.cell
def _(mo):
    mo.md(
        """
        # Clay County Livestock Auction Analysis

        Interactive analysis of cattle prices from the Clay County Livestock Auction in Lineville, AL.
        Data spans from 2019 to 2025.
        """
    )
    return


@app.cell
def _(df, mo):
    # Summary stats
    total_records = len(df)
    date_range = f"{df['auction_date'].min().date()} to {df['auction_date'].max().date()}"
    total_auctions = df["auction_date"].nunique()

    mo.md(
        f"""
        ## Data Overview

        | Metric | Value |
        |--------|-------|
        | Total Records | {total_records:,} |
        | Date Range | {date_range} |
        | Total Auction Days | {total_auctions} |
        """
    )
    return date_range, total_auctions, total_records


@app.cell
def _(df, mo):
    # Create filters
    categories = ["All"] + sorted(df["category"].unique().tolist())
    cattle_types = ["All"] + sorted(df["cattle_type"].unique().tolist())
    years = ["All"] + sorted([int(y) for y in df["year"].unique().tolist()])

    category_select = mo.ui.dropdown(
        options=categories, value="All", label="Category"
    )
    cattle_type_select = mo.ui.dropdown(
        options=cattle_types, value="All", label="Cattle Type"
    )
    year_select = mo.ui.dropdown(
        options=[str(y) for y in years], value="All", label="Year"
    )

    mo.md("## Filters")
    return (
        categories,
        category_select,
        cattle_type_select,
        cattle_types,
        year_select,
        years,
    )


@app.cell
def _(category_select, cattle_type_select, mo, year_select):
    mo.hstack([category_select, cattle_type_select, year_select])
    return


@app.cell
def _(category_select, cattle_type_select, df, year_select):
    # Apply filters
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
    mo.md(f"**Showing {len(filtered_df):,} records**")
    return


@app.cell
def _(mo):
    mo.md("## Average Price Trends Over Time")
    return


@app.cell
def _(alt, filtered_df):
    # Calculate monthly averages
    monthly_avg = (
        filtered_df[filtered_df["avg_price"] > 0]
        .groupby(["year_month", "cattle_type"])
        .agg({"avg_price": "mean", "head_count": "sum"})
        .reset_index()
    )

    # Price trend chart
    price_chart = (
        alt.Chart(monthly_avg)
        .mark_line(point=True)
        .encode(
            x=alt.X("year_month:O", title="Month", axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("avg_price:Q", title="Average Price ($/cwt)"),
            color=alt.Color("cattle_type:N", title="Cattle Type"),
            tooltip=["year_month", "cattle_type", "avg_price:Q", "head_count:Q"],
        )
        .properties(width=800, height=400, title="Monthly Average Prices by Cattle Type")
        .interactive()
    )
    price_chart
    return monthly_avg, price_chart


@app.cell
def _(mo):
    mo.md("## Price Distribution by Weight Class")
    return


@app.cell
def _(alt, filtered_df, pd):
    # Create weight classes
    weight_df = filtered_df[filtered_df["avg_weight"] > 0].copy()
    weight_df["weight_class"] = pd.cut(
        weight_df["avg_weight"],
        bins=[0, 300, 400, 500, 600, 700, 800, 1000, 2000],
        labels=["<300", "300-400", "400-500", "500-600", "600-700", "700-800", "800-1000", ">1000"],
    )

    # Box plot by weight class
    weight_price_chart = (
        alt.Chart(weight_df[weight_df["avg_price"] > 0])
        .mark_boxplot()
        .encode(
            x=alt.X("weight_class:O", title="Weight Class (lbs)"),
            y=alt.Y("avg_price:Q", title="Price ($/cwt)"),
            color=alt.Color("cattle_type:N", title="Cattle Type"),
        )
        .properties(width=800, height=400, title="Price Distribution by Weight Class")
    )
    weight_price_chart
    return weight_df, weight_price_chart


@app.cell
def _(mo):
    mo.md("## Volume Trends")
    return


@app.cell
def _(alt, filtered_df):
    # Volume by month
    volume_monthly = (
        filtered_df.groupby(["year_month", "category"])
        .agg({"head_count": "sum"})
        .reset_index()
    )

    volume_chart = (
        alt.Chart(volume_monthly)
        .mark_bar()
        .encode(
            x=alt.X("year_month:O", title="Month", axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("head_count:Q", title="Head Count"),
            color=alt.Color("category:N", title="Category"),
            tooltip=["year_month", "category", "head_count:Q"],
        )
        .properties(width=800, height=300, title="Monthly Volume by Category")
        .interactive()
    )
    volume_chart
    return volume_chart, volume_monthly


@app.cell
def _(mo):
    mo.md("## Year-over-Year Comparison")
    return


@app.cell
def _(alt, filtered_df):
    # Yearly averages by cattle type
    yearly_avg = (
        filtered_df[filtered_df["avg_price"] > 0]
        .groupby(["year", "cattle_type"])
        .agg({"avg_price": "mean", "head_count": "sum"})
        .reset_index()
    )

    yearly_chart = (
        alt.Chart(yearly_avg)
        .mark_bar()
        .encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y("avg_price:Q", title="Average Price ($/cwt)"),
            color=alt.Color("cattle_type:N", title="Cattle Type"),
            xOffset="cattle_type:N",
            tooltip=["year", "cattle_type", "avg_price:Q", "head_count:Q"],
        )
        .properties(width=800, height=400, title="Average Prices by Year and Cattle Type")
    )
    yearly_chart
    return yearly_avg, yearly_chart


@app.cell
def _(mo):
    mo.md("## Weight vs Price Scatter Plot")
    return


@app.cell
def _(mo):
    # Slider for recency weighting
    halflife_slider = mo.ui.slider(
        start=6,
        stop=60,
        value=24,
        step=6,
        label="Half-life (months)",
    )
    halflife_slider
    return (halflife_slider,)


@app.cell
def _(filtered_df, halflife_slider, pd, px):
    import numpy as np
    import statsmodels.api as sm
    import plotly.graph_objects as go

    # Filter for valid data points and create combined market type
    scatter_df_full = filtered_df[
        (filtered_df["avg_weight"] > 0) & (filtered_df["avg_price"] > 0)
    ].copy()
    scatter_df_full["market_type"] = scatter_df_full["category"] + " " + scatter_df_full["cattle_type"]

    # Calculate weights based on recency (exponential decay)
    max_date = scatter_df_full["auction_date"].max()
    scatter_df_full["days_ago"] = (max_date - scatter_df_full["auction_date"]).dt.days
    halflife_days = halflife_slider.value * 30  # Convert months to days
    scatter_df_full["weight"] = np.exp(-np.log(2) * scatter_df_full["days_ago"] / halflife_days)

    # Calculate weighted linear regression for each market type
    regression_results = []
    trendline_data = []

    for market_type in sorted(scatter_df_full["market_type"].unique()):
        subset = scatter_df_full[scatter_df_full["market_type"] == market_type]
        if len(subset) > 10:
            X = sm.add_constant(subset["avg_weight"])
            y = subset["avg_price"]
            weights = subset["weight"]

            # Weighted least squares
            model = sm.WLS(y, X, weights=weights)
            results = model.fit()

            intercept, slope = results.params
            r_squared = results.rsquared

            regression_results.append({
                "market_type": market_type,
                "slope": slope,
                "intercept": intercept,
                "r_squared": r_squared,
                "n": len(subset),
            })

            # Generate trendline points
            x_range = np.linspace(subset["avg_weight"].min(), subset["avg_weight"].max(), 100)
            y_pred = intercept + slope * x_range
            trendline_data.append({
                "market_type": market_type,
                "x": x_range,
                "y": y_pred,
            })

    regression_df = pd.DataFrame(regression_results)

    # Sample data for plotting (max 400 points per market type)
    scatter_df = scatter_df_full.groupby("market_type", group_keys=False).apply(
        lambda x: x.sample(n=min(len(x), 400), random_state=42)
    )

    # Create Plotly figure
    scatter_chart = px.scatter(
        scatter_df,
        x="avg_weight",
        y="avg_price",
        color="market_type",
        labels={
            "avg_weight": "Average Weight (lbs)",
            "avg_price": "Price ($/cwt)",
            "market_type": "Market Type",
        },
        title=f"Weight vs Price by Market Type (Recency-Weighted Regression, {halflife_slider.value}mo half-life)",
        hover_data=["auction_date", "head_count"],
        opacity=0.6,
    )

    # Add weighted trendlines
    colors = px.colors.qualitative.Plotly
    for i, trend in enumerate(trendline_data):
        scatter_chart.add_trace(
            go.Scatter(
                x=trend["x"],
                y=trend["y"],
                mode="lines",
                name=f"{trend['market_type']} (trend)",
                line=dict(color=colors[i % len(colors)], width=3),
                showlegend=False,
            )
        )

    scatter_chart.update_layout(
        width=900,
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    scatter_chart
    return go, np, regression_df, scatter_chart, scatter_df, scatter_df_full, sm, trendline_data


@app.cell
def _(halflife_slider, mo, regression_df):
    # Display regression equations
    if len(regression_df) > 0:
        eq_text = f"### Recency-Weighted Regression Equations ({halflife_slider.value}-month half-life)\n\n"
        eq_text += "| Market Type | Equation | R² | N |\n"
        eq_text += "|-------------|----------|----|----|"
        for _, row in regression_df.iterrows():
            eq_text += f"\n| {row['market_type']} | y = {row['slope']:.4f}x + {row['intercept']:.2f} | {row['r_squared']:.4f} | {row['n']:,} |"
        mo.md(eq_text)
    return (eq_text,)


@app.cell
def _(mo):
    mo.md("## Summary Statistics")
    return


@app.cell
def _(filtered_df, mo):
    # Summary stats table
    summary = (
        filtered_df[filtered_df["avg_price"] > 0]
        .groupby(["category", "cattle_type"])
        .agg(
            {
                "avg_price": ["mean", "min", "max", "std"],
                "head_count": "sum",
                "avg_weight": "mean",
            }
        )
        .round(2)
    )
    summary.columns = ["Avg Price", "Min Price", "Max Price", "Price Std", "Total Head", "Avg Weight"]
    summary = summary.reset_index()

    mo.ui.table(summary)
    return (summary,)


@app.cell
def _(mo):
    mo.md("## Raw Data Explorer")
    return


@app.cell
def _(filtered_df, mo):
    display_df = filtered_df[
        [
            "auction_date",
            "category",
            "cattle_type",
            "grade",
            "head_count",
            "avg_weight",
            "avg_price",
        ]
    ].head(100).copy()
    display_df["auction_date"] = display_df["auction_date"].astype(str)
    mo.ui.table(display_df)
    return (display_df,)


if __name__ == "__main__":
    app.run()
