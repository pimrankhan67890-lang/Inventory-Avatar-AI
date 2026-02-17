import pandas as pd
from prophet import Prophet

DATE_CANDIDATES = ["date", "order_date", "bill_date", "invoice_date"]
QTY_CANDIDATES = ["units_sold", "qty", "quantity", "sold", "units"]
PRODUCT_CANDIDATES = ["product", "item", "sku", "part", "name"]


def find_column(df, candidates):
    for c in df.columns:
        clean = c.lower().strip()
        if clean in candidates:
            return c
    return None


def run_forecast(product_df):
    product_df = product_df.groupby("date")["units_sold"].sum().reset_index()
    product_df.columns = ["ds", "y"]
    product_df["ds"] = pd.to_datetime(product_df["ds"])

    model = Prophet()
    model.fit(product_df)

    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)

    demand30 = forecast.tail(30)["yhat"].sum()
    return demand30, forecast[["ds", "yhat"]]


def forecast_universal(file):
    df = pd.read_csv(file)
    df.columns = [c.lower().strip() for c in df.columns]

    date_col = find_column(df, DATE_CANDIDATES)
    qty_col = find_column(df, QTY_CANDIDATES)
    prod_col = find_column(df, PRODUCT_CANDIDATES)

    if not date_col or not qty_col:
        raise ValueError("Could not detect date and quantity columns")

    if not prod_col:
        df["product"] = "Product_A"
        prod_col = "product"

    df = df.rename(columns={
        date_col: "date",
        qty_col: "units_sold",
        prod_col: "product"
    })

    results = {}

    for product in df["product"].unique():
        sub = df[df["product"] == product]
        demand, fc = run_forecast(sub)
        results[product] = (demand, fc)

    return results