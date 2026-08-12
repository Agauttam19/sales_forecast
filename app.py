import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="Sales Forecasting Dashboard", layout="wide")

# --- Load data ---
conn = sqlite3.connect("database/sales.db")
df = pd.read_sql("SELECT * FROM sales", conn)
conn.close()

df["Order_Date"] = pd.to_datetime(df["Order_Date"])
forecast = pd.read_csv("data/forecast_output.csv")
forecast["ds"] = pd.to_datetime(forecast["ds"])

# --- Sidebar filters ---
st.sidebar.header("Filters")
region_filter = st.sidebar.multiselect("Region", options=df["Region"].unique(), default=df["Region"].unique())
category_filter = st.sidebar.multiselect("Category", options=df["Category"].unique(), default=df["Category"].unique())

filtered_df = df[df["Region"].isin(region_filter) & df["Category"].isin(category_filter)]

# --- Title ---
st.title("📊 Sales Forecasting & Business Performance Dashboard")

# --- KPI cards ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sales", f"${filtered_df['Sales'].sum():,.0f}")
col2.metric("Total Profit", f"${filtered_df['Profit'].sum():,.0f}")
col3.metric("Total Orders", f"{filtered_df['Order_ID'].nunique():,}")
margin = (filtered_df['Profit'].sum() / filtered_df['Sales'].sum()) * 100
col4.metric("Profit Margin", f"{margin:.1f}%")

st.markdown("---")

# --- Monthly sales trend ---
st.subheader("Monthly Sales Trend")
monthly = filtered_df.groupby(filtered_df["Order_Date"].dt.to_period("M"))["Sales"].sum().reset_index()
monthly["Order_Date"] = monthly["Order_Date"].dt.to_timestamp()
fig = px.line(monthly, x="Order_Date", y="Sales", title="Historical Sales (filtered)")
st.plotly_chart(fig, use_container_width=True)

# --- Forecast section (separate, company-wide, not affected by filters) ---
st.markdown("---")
st.subheader("📈 Sales Forecast — Next 6 Months (Company-wide)")
st.caption("Forecast is based on total company sales and is not affected by the sidebar filters.")

fig_forecast = px.line(forecast, x="ds", y="yhat", title="Predicted Sales")
fig_forecast.add_scatter(x=forecast["ds"], y=forecast["yhat_upper"], mode="lines", 
                          line=dict(width=0), showlegend=False)
fig_forecast.add_scatter(x=forecast["ds"], y=forecast["yhat_lower"], mode="lines", 
                          line=dict(width=0), fill="tonexty", fillcolor="rgba(0,100,255,0.15)",
                          name="Confidence Interval")
st.plotly_chart(fig_forecast, use_container_width=True)

# Show just the future predictions as a table too
st.write("**Next 6 months predicted values:**")
future_only = forecast[forecast["ds"] > monthly["Order_Date"].max()][["ds", "yhat", "yhat_lower", "yhat_upper"]]
future_only.columns = ["Month", "Predicted Sales", "Lower Bound", "Upper Bound"]
future_only["Month"] = future_only["Month"].dt.strftime("%Y-%m")
st.dataframe(future_only.style.format({"Predicted Sales": "${:,.0f}", "Lower Bound": "${:,.0f}", "Upper Bound": "${:,.0f}"}), use_container_width=True)

# --- Two-column layout: Region + Category ---
col5, col6 = st.columns(2)

with col5:
    st.subheader("Sales by Region")
    region_sales = filtered_df.groupby("Region")["Sales"].sum().reset_index()
    fig2 = px.bar(region_sales, x="Region", y="Sales", color="Region")
    st.plotly_chart(fig2, use_container_width=True)

with col6:
    st.subheader("Profit by Category")
    cat_profit = filtered_df.groupby("Category")["Profit"].sum().reset_index()
    fig3 = px.bar(cat_profit, x="Category", y="Profit", color="Category")
    st.plotly_chart(fig3, use_container_width=True)

# --- Top products table ---
st.subheader("Top 10 Products by Sales")
top_products = filtered_df.groupby("Product_Name")["Sales"].sum().nlargest(10).reset_index()
st.dataframe(top_products, use_container_width=True)
# --- Heatmap: Sales by Month vs Category ---
st.subheader("Sales Heatmap: Month vs Category")

heatmap_df = filtered_df.copy()
heatmap_df["Month"] = heatmap_df["Order_Date"].dt.strftime("%Y-%m")

heatmap_data = heatmap_df.groupby(["Month", "Category"])["Sales"].sum().reset_index()
heatmap_pivot = heatmap_data.pivot(index="Category", columns="Month", values="Sales").fillna(0)

fig4 = px.imshow(
    heatmap_pivot,
    labels=dict(x="Month", y="Category", color="Sales ($)"),
    aspect="auto",
    color_continuous_scale="YlGnBu"
)
fig4.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig4, use_container_width=True)