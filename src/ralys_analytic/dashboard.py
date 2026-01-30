import streamlit as st
import pandas as pd
from defillama_sdk import DefiLlama

from metric import tvl
from metric import revenue
from metric import price

st.set_page_config(page_title="Rayls Token Analytics", layout="wide")

st.title("Rayls Token Analytics Dashboard")


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    client = DefiLlama()

    # Metadata: (name, display_name, token_supply, price_address, type)
    # type: "protocol" or "chain"
    metadata = [
        ("zksync_era", "zkSync Era", 21_000_000_000, "era:0x5A7d6b2F92C77FAD6CCaBd7EE0624E64907Eaf3E", "protocol"),
        ("plume_mainnet", "Plume Mainnet", 10_000_000_000, "ethereum:0x4C1746A800D224393fE2470C70A35717eD4eA5F1", "protocol"),
        ("avalanche", "Avalanche", 715_740_000, "coingecko:avalanche-2", "protocol"),
        ("ondo_finance", "Ondo Finance", 10_000_000_000, "ethereum:0xfaba6f8e4a5e8ab82f62fe7c39859fa577269be3", "protocol"),
        ("ondo_yield_assets", "Ondo Yield Assets", 1_250_000_000, "ethereum:0x96f6ef951840721adbf46ac996b59e0235cb985c", "protocol"),
        ("polygon", "Polygon", 10_000_000_000, "ethereum:0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0", "chain"),
    ]

    def get_2025_revenue(revenue_data):
        annual_data = revenue.annualRevenue(revenue_data)
        for year, total in annual_data:
            if year == "2025":
                return total
        return None

    results = []

    for item in metadata:
        name, display_name, token_supply, price_address, item_type = item

        try:
            # Get current price
            current_price = price.getLatestTokenPrice(client, [price_address])

            # Calculate FDV
            fdv = current_price * token_supply

            # Get 2025 revenue
            if item_type == "protocol":
                revenue_data = revenue.getRevenueByProtocol(client, display_name)
            else:
                revenue_data = revenue.getRevenueByChain(client, display_name)

            revenue_2025 = get_2025_revenue(revenue_data)

            # Calculate multiplier
            multiplier = fdv / revenue_2025 if revenue_2025 and revenue_2025 > 0 else None

            results.append({
                "Project": display_name,
                "Current Price ($)": current_price,
                "Token Supply": token_supply,
                "FDV ($)": fdv,
                "Revenue 2025 ($)": revenue_2025,
                "Multiplier (FDV/Revenue)": multiplier
            })
        except Exception as e:
            results.append({
                "Project": display_name,
                "Current Price ($)": None,
                "Token Supply": token_supply,
                "FDV ($)": None,
                "Revenue 2025 ($)": None,
                "Multiplier (FDV/Revenue)": None
            })

    # Add Rayls token
    try:
        rayls_price_data = price.getRaylsPrice()
        rayls_price = rayls_price_data['price_usd']
        rayls_supply = 10_000_000_000
        rayls_fdv = rayls_price * rayls_supply
        rayls_revenue = 2_000_000  # Hardcoded for now
        rayls_multiplier = rayls_fdv / rayls_revenue

        results.append({
            "Project": "Rayls (RLS)",
            "Current Price ($)": rayls_price,
            "Token Supply": rayls_supply,
            "FDV ($)": rayls_fdv,
            "Revenue 2025 ($)": rayls_revenue,
            "Multiplier (FDV/Revenue)": rayls_multiplier
        })
    except Exception as e:
        st.warning(f"Could not fetch Rayls token data: {e}")

    return pd.DataFrame(results)


# Load data
with st.spinner("Loading data from APIs..."):
    df = load_data()

# Format the dataframe for display
def format_currency(val):
    if val is None or pd.isna(val):
        return "N/A"
    if val >= 1_000_000_000:
        return f"${val/1_000_000_000:,.2f}B"
    elif val >= 1_000_000:
        return f"${val/1_000_000:,.2f}M"
    elif val >= 1_000:
        return f"${val/1_000:,.2f}K"
    else:
        return f"${val:,.4f}"

def format_supply(val):
    if val is None or pd.isna(val):
        return "N/A"
    if val >= 1_000_000_000:
        return f"{val/1_000_000_000:,.2f}B"
    elif val >= 1_000_000:
        return f"{val/1_000_000:,.2f}M"
    else:
        return f"{val:,.0f}"

def format_multiplier(val):
    if val is None or pd.isna(val):
        return "N/A"
    return f"{val:,.2f}x"

# Create formatted display dataframe
display_df = df.copy()
display_df["Current Price ($)"] = df["Current Price ($)"].apply(lambda x: f"${x:,.6f}" if x and not pd.isna(x) else "N/A")
display_df["Token Supply"] = df["Token Supply"].apply(format_supply)
display_df["FDV ($)"] = df["FDV ($)"].apply(format_currency)
display_df["Revenue 2025 ($)"] = df["Revenue 2025 ($)"].apply(format_currency)
display_df["Multiplier (FDV/Revenue)"] = df["Multiplier (FDV/Revenue)"].apply(format_multiplier)

# Display the table
st.subheader("Project Comparison Table")
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Project": st.column_config.TextColumn("Project", width="medium"),
        "Current Price ($)": st.column_config.TextColumn("Current Price", width="small"),
        "Token Supply": st.column_config.TextColumn("Token Supply", width="small"),
        "FDV ($)": st.column_config.TextColumn("FDV", width="small"),
        "Revenue 2025 ($)": st.column_config.TextColumn("Revenue 2025", width="small"),
        "Multiplier (FDV/Revenue)": st.column_config.TextColumn("Multiplier", width="small"),
    }
)

# Summary metrics
st.subheader("Summary Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_multiplier = df["Multiplier (FDV/Revenue)"].dropna().mean()
    st.metric("Average Multiplier", f"{avg_multiplier:,.2f}x" if avg_multiplier else "N/A")

with col2:
    min_multiplier = df["Multiplier (FDV/Revenue)"].dropna().min()
    st.metric("Min Multiplier", f"{min_multiplier:,.2f}x" if min_multiplier else "N/A")

with col3:
    max_multiplier = df["Multiplier (FDV/Revenue)"].dropna().max()
    st.metric("Max Multiplier", f"{max_multiplier:,.2f}x" if max_multiplier else "N/A")

with col4:
    rayls_row = df[df["Project"] == "Rayls (RLS)"]
    if not rayls_row.empty:
        rayls_mult = rayls_row["Multiplier (FDV/Revenue)"].values[0]
        st.metric("Rayls Multiplier", f"{rayls_mult:,.2f}x" if rayls_mult else "N/A")

# Refresh button
if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()
