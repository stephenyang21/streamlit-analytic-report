import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from defillama_sdk import DefiLlama

from metric import revenue
from metric import price

st.set_page_config(
    page_title="Rayls Token Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for enhanced design
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    .main-header h1 {
        color: #ffffff;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }

    .main-header p {
        color: #e2e8f0;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        margin-bottom: 0;
    }

    /* Card styling */
    .metric-card {
        background: linear-gradient(145deg, #1e1e2e, #252536);
        border: 1px solid #3a3a4a;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }

    .metric-card-highlight {
        background: linear-gradient(145deg, #1a365d, #2a4a7f);
        border: 2px solid #4299e1;
    }

    /* These classes are for elements inside dark cards only */
    .metric-label {
        color: #cbd5e1;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }

    .metric-value {
        color: #f8fafc;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .metric-delta-positive {
        color: #68d391;
        font-size: 0.95rem;
        font-weight: 600;
    }

    .metric-delta-negative {
        color: #feb2b2;
        font-size: 0.95rem;
        font-weight: 600;
    }

    /* Dark card specific - bright text for dark backgrounds */
    .token-card, .main-header {
        color: #f8fafc;
    }

    /* Token card styling */
    .token-card {
        background: linear-gradient(145deg, #1e1e2e, #252536);
        border: 1px solid #3a3a4a;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }

    .token-card-rayls {
        background: linear-gradient(145deg, #1a365d, #234876);
        border: 2px solid #4299e1;
        box-shadow: 0 4px 20px rgba(66, 153, 225, 0.3);
    }

    .token-name {
        color: #f8fafc;
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .token-price {
        color: #f8fafc;
        font-size: 2rem;
        font-weight: 700;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    }

    .token-fdv {
        color: #e2e8f0;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }

    .change-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }

    .change-positive {
        background-color: rgba(72, 187, 120, 0.25);
        color: #68d391;
    }

    .change-negative {
        background-color: rgba(252, 129, 129, 0.25);
        color: #feb2b2;
    }

    .change-neutral {
        background-color: rgba(100, 116, 139, 0.2);
        color: #e2e8f0;
    }

    /* Section headers - inherit color from theme */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #e2e8f0;
    }

    /* Table styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
    }

    .stTabs [aria-selected="true"] {
        background-color: #4299e1 !important;
        border-color: #4299e1 !important;
        color: #ffffff !important;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #3182ce, #2563eb);
        color: #ffffff !important;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
        color: #ffffff !important;
    }

    /* Metric component styling */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.95rem;
    }

    /* Divider styling */
    hr {
        border-color: #475569;
        margin: 2rem 0;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>Rayls Token Analytics</h1>
    <p>Real-time price tracking and valuation metrics for blockchain protocols</p>
</div>
""", unsafe_allow_html=True)

# Navigation tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Project Comparison", "💹 Market Condition", "📈 Valuation Analysis", "📉 Price Performance"])


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    client = DefiLlama()

    # Metadata: (name, display_name, token_supply, circulating_token, coingecko_id, type, revenue_override)
    metadata = [
        ("zksync_era", "zkSync Era", 21_000_000_000, 8_620_000_000, "zksync", "protocol", None),
        ("plume_mainnet", "Plume Mainnet", 10_000_000_000, 4_800_000_000, "plume", "protocol", None),
        ("avalanche", "Avalanche", 715_740_000, 431_720_000, "avalanche-2", "protocol", None),
        ("ondo_finance", "Ondo Finance", 10_000_000_000, 4_860_000_000, "ondo-finance", "protocol", None),
        ("ondo_yield_assets", "Ondo Yield Assets", 1_250_000_000, 628_940_000, "ondo-us-dollar-yield", "protocol", None),
        ("polygon", "Polygon", 10_000_000_000, 1_910_000_000, "polygon-ecosystem-token", "chain", None),
        ("rayls", "Rayls (RLS)", 10_000_000_000, 1_500_000_000, "rls", "protocol", 2_000_000),
    ]

    def get_2025_revenue(revenue_data):
        annual_data = revenue.annualRevenue(revenue_data)
        for year, total in annual_data:
            if year == "2025":
                return total
        return None

    # Fetch CoinGecko prices for non-Rayls tokens
    coingecko_ids = [item[4] for item in metadata if item[4] != "rls"]
    price_data_batch = price.getCoingeckoPricesBatch(coingecko_ids)

    # Fetch Rayls price from CoinMarketCap
    try:
        rayls_price_data = price.getRaylsPrice()
        price_data_batch["rls"] = {
            "price": rayls_price_data.get("price_usd"),
            "market_cap": rayls_price_data.get("market_cap"),
            "percent_change_24h": rayls_price_data.get("percent_change_24h"),
            "percent_change_7d": rayls_price_data.get("percent_change_7d"),
            "percent_change_30d": rayls_price_data.get("percent_change_30d"),
        }
    except Exception:
        price_data_batch["rls"] = {
            "price": None,
            "market_cap": None,
            "percent_change_24h": None,
            "percent_change_7d": None,
            "percent_change_30d": None,
        }

    results = []

    for item in metadata:
        _, display_name, token_supply, circulating_token, coingecko_id, item_type, revenue_override = item

        try:
            price_data = price_data_batch.get(coingecko_id, {})
            current_price = price_data.get('price')
            market_cap = price_data.get('market_cap')
            fdv = current_price * token_supply if current_price else None

            # Get revenue data
            revenue_data = None
            revenue_growth_30d = None
            revenue_growth_90d = None

            if revenue_override is not None:
                revenue_2025 = revenue_override
            elif item_type == "protocol":
                revenue_data = revenue.getRevenueByProtocol(client, display_name)
                revenue_2025 = get_2025_revenue(revenue_data)
            else:
                revenue_data = revenue.getRevenueByChain(client, display_name)
                revenue_2025 = get_2025_revenue(revenue_data)

            # Calculate revenue growth if we have revenue data (not for Rayls)
            if revenue_data is not None:
                revenue_growth_30d = revenue.getRevenueGrowth(revenue_data, days=30)
                revenue_growth_90d = revenue.getRevenueGrowth(revenue_data, days=90)

            multiplier = fdv / revenue_2025 if fdv and revenue_2025 and revenue_2025 > 0 else None

            # Calculate circulating market cap
            circulating_market_cap = current_price * circulating_token if current_price else None

            results.append({
                "Project": display_name,
                "Current Price ($)": current_price,
                "Token Supply": token_supply,
                "Circulating Supply": circulating_token,
                "FDV ($)": fdv,
                "Market Cap ($)": market_cap,
                "Circulating Market Cap ($)": circulating_market_cap,
                "Revenue 2025 ($)": revenue_2025,
                "Multiplier (FDV/Revenue)": multiplier,
                "Revenue Growth 30d (%)": revenue_growth_30d,
                "Revenue Growth 90d (%)": revenue_growth_90d,
                "Change 24h (%)": price_data.get('percent_change_24h'),
                "Change 7d (%)": price_data.get('percent_change_7d'),
                "Change 30d (%)": price_data.get('percent_change_30d'),
            })
        except Exception:
            results.append({
                "Project": display_name,
                "Current Price ($)": None,
                "Token Supply": token_supply,
                "Circulating Supply": circulating_token,
                "FDV ($)": None,
                "Market Cap ($)": None,
                "Circulating Market Cap ($)": None,
                "Revenue 2025 ($)": None,
                "Multiplier (FDV/Revenue)": None,
                "Revenue Growth 30d (%)": None,
                "Revenue Growth 90d (%)": None,
                "Change 24h (%)": None,
                "Change 7d (%)": None,
                "Change 30d (%)": None,
            })

    return pd.DataFrame(results)


# Load data
with st.spinner("Loading data from APIs..."):
    df = load_data()


# Helper functions
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


def format_percent_change(val):
    if val is None or pd.isna(val):
        return "N/A"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.2f}%"


def color_percent_change(val):
    if val is None or pd.isna(val) or val == "N/A":
        return "color: #64748b"
    if isinstance(val, str):
        if val.startswith("+") or (val[0].isdigit() and not val.startswith("-")):
            return "color: #16a34a; font-weight: 600"
        elif val.startswith("-"):
            return "color: #dc2626; font-weight: 600"
        return "color: #64748b"
    if val >= 0:
        return "color: #16a34a; font-weight: 600"
    else:
        return "color: #dc2626; font-weight: 600"


def get_change_badge(val):
    if val is None or pd.isna(val):
        return '<span class="change-badge change-neutral">N/A</span>'
    sign = "+" if val >= 0 else ""
    css_class = "change-positive" if val >= 0 else "change-negative"
    return f'<span class="change-badge {css_class}">{sign}{val:.2f}%</span>'


# Tab 1: Project Comparison
with tab1:
    # Rayls highlight section
    rayls_row = df[df["Project"] == "Rayls (RLS)"]
    if not rayls_row.empty:
        rayls_data = rayls_row.iloc[0]

        st.markdown('<div class="section-header">Rayls (RLS) Overview</div>', unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            price_val = rayls_data["Current Price ($)"]
            st.metric(
                label="Current Price",
                value=f"${price_val:,.6f}" if price_val and not pd.isna(price_val) else "N/A",
                delta=f"{rayls_data['Change 24h (%)']:+.2f}%" if rayls_data['Change 24h (%)'] and not pd.isna(rayls_data['Change 24h (%)']) else None
            )

        with col2:
            st.metric(
                label="FDV",
                value=format_currency(rayls_data["FDV ($)"])
            )

        with col3:
            st.metric(
                label="Revenue 2025",
                value=format_currency(rayls_data["Revenue 2025 ($)"])
            )

        with col4:
            st.metric(
                label="Multiplier",
                value=format_multiplier(rayls_data["Multiplier (FDV/Revenue)"])
            )

        with col5:
            change_7d = rayls_data["Change 7d (%)"]
            change_30d = rayls_data["Change 30d (%)"]
            st.markdown("**Price Changes**")
            st.markdown(f"7d: {get_change_badge(change_7d)} 30d: {get_change_badge(change_30d)}", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

    # Comparison table
    st.markdown('<div class="section-header">All Projects Comparison</div>', unsafe_allow_html=True)

    # Create formatted display dataframe (exclude revenue growth columns)
    display_cols = ["Project", "Current Price ($)", "Token Supply", "FDV ($)", "Revenue 2025 ($)",
                    "Multiplier (FDV/Revenue)", "Change 24h (%)", "Change 7d (%)", "Change 30d (%)"]
    display_df = df[display_cols].copy()
    display_df["Current Price ($)"] = df["Current Price ($)"].apply(lambda x: f"${x:,.6f}" if x and not pd.isna(x) else "N/A")
    display_df["Token Supply"] = df["Token Supply"].apply(format_supply)
    display_df["FDV ($)"] = df["FDV ($)"].apply(format_currency)
    display_df["Revenue 2025 ($)"] = df["Revenue 2025 ($)"].apply(format_currency)
    display_df["Multiplier (FDV/Revenue)"] = df["Multiplier (FDV/Revenue)"].apply(format_multiplier)
    display_df["Change 24h (%)"] = df["Change 24h (%)"].apply(format_percent_change)
    display_df["Change 7d (%)"] = df["Change 7d (%)"].apply(format_percent_change)
    display_df["Change 30d (%)"] = df["Change 30d (%)"].apply(format_percent_change)

    # Apply styling for color
    change_columns = ["Change 24h (%)", "Change 7d (%)", "Change 30d (%)"]
    styled_df = display_df.style.map(color_percent_change, subset=change_columns)

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=320,
        column_config={
            "Project": st.column_config.TextColumn("Project", width="medium"),
            "Current Price ($)": st.column_config.TextColumn("Price", width="small"),
            "Token Supply": st.column_config.TextColumn("Supply", width="small"),
            "FDV ($)": st.column_config.TextColumn("FDV", width="small"),
            "Revenue 2025 ($)": st.column_config.TextColumn("Revenue '25", width="small"),
            "Multiplier (FDV/Revenue)": st.column_config.TextColumn("Multiplier", width="small"),
            "Change 24h (%)": st.column_config.TextColumn("24h", width="small"),
            "Change 7d (%)": st.column_config.TextColumn("7d", width="small"),
            "Change 30d (%)": st.column_config.TextColumn("30d", width="small"),
        }
    )

    # Market Cap comparison table
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Market Cap Comparison</div>', unsafe_allow_html=True)

    # Create market cap display dataframe
    mcap_cols = ["Project", "Current Price ($)", "Circulating Supply", "Token Supply", "Circulating Market Cap ($)", "FDV ($)"]
    mcap_df = df[mcap_cols].copy()
    mcap_df["Current Price ($)"] = df["Current Price ($)"].apply(lambda x: f"${x:,.6f}" if x and not pd.isna(x) else "N/A")
    mcap_df["Circulating Supply"] = df["Circulating Supply"].apply(format_supply)
    mcap_df["Token Supply"] = df["Token Supply"].apply(format_supply)
    mcap_df["Circulating Market Cap ($)"] = df["Circulating Market Cap ($)"].apply(format_currency)
    mcap_df["FDV ($)"] = df["FDV ($)"].apply(format_currency)

    # Sort by circulating market cap descending
    mcap_df_sorted = mcap_df.copy()
    mcap_df_sorted["_sort_key"] = df["Circulating Market Cap ($)"]
    mcap_df_sorted = mcap_df_sorted.sort_values("_sort_key", ascending=False).drop(columns=["_sort_key"])

    st.dataframe(
        mcap_df_sorted,
        use_container_width=True,
        hide_index=True,
        height=320,
        column_config={
            "Project": st.column_config.TextColumn("Project", width="medium"),
            "Current Price ($)": st.column_config.TextColumn("Price", width="small"),
            "Circulating Supply": st.column_config.TextColumn("Circ. Supply", width="small"),
            "Token Supply": st.column_config.TextColumn("Total Supply", width="small"),
            "Circulating Market Cap ($)": st.column_config.TextColumn("Circ. Market Cap", width="medium"),
            "FDV ($)": st.column_config.TextColumn("FDV", width="small"),
        }
    )

    # Summary metrics
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Valuation Metrics Summary</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_multiplier = df["Multiplier (FDV/Revenue)"].dropna().mean()
        st.metric("Average Multiplier", f"{avg_multiplier:,.2f}x" if avg_multiplier else "N/A")

    with col2:
        min_multiplier = df["Multiplier (FDV/Revenue)"].dropna().min()
        min_project = df.loc[df["Multiplier (FDV/Revenue)"].idxmin(), "Project"] if not df["Multiplier (FDV/Revenue)"].dropna().empty else "N/A"
        st.metric("Lowest Multiplier", f"{min_multiplier:,.2f}x" if min_multiplier else "N/A", help=f"Project: {min_project}")

    with col3:
        max_multiplier = df["Multiplier (FDV/Revenue)"].dropna().max()
        max_project = df.loc[df["Multiplier (FDV/Revenue)"].idxmax(), "Project"] if not df["Multiplier (FDV/Revenue)"].dropna().empty else "N/A"
        st.metric("Highest Multiplier", f"{max_multiplier:,.2f}x" if max_multiplier else "N/A", help=f"Project: {max_project}")

    with col4:
        if not rayls_row.empty:
            rayls_mult = rayls_row["Multiplier (FDV/Revenue)"].values[0]
            comparison = ""
            if rayls_mult and avg_multiplier:
                diff = ((rayls_mult / avg_multiplier) - 1) * 100
                comparison = f"{diff:+.1f}% vs avg"
            st.metric("Rayls Multiplier", f"{rayls_mult:,.2f}x" if rayls_mult else "N/A", delta=comparison if comparison else None)


# Tab 2: Market Condition
with tab2:
    st.markdown('<div class="section-header">Live Token Prices</div>', unsafe_allow_html=True)

    # Rayls featured card first
    rayls_row = df[df["Project"] == "Rayls (RLS)"]
    if not rayls_row.empty:
        rayls_data = rayls_row.iloc[0]

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            price_val = rayls_data["Current Price ($)"]
            change_24h = rayls_data["Change 24h (%)"]

            st.markdown(f"""
            <div class="token-card token-card-rayls">
                <div class="token-name">⭐ Rayls (RLS) - Featured</div>
                <div class="token-price">${price_val:,.6f}</div>
                <div class="token-fdv">FDV: {format_currency(rayls_data["FDV ($)"])}</div>
                <div style="margin-top: 1rem;">
                    {get_change_badge(rayls_data["Change 24h (%)"])} 24h
                    {get_change_badge(rayls_data["Change 7d (%)"])} 7d
                    {get_change_badge(rayls_data["Change 30d (%)"])} 30d
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Other tokens grid
    other_tokens = df[df["Project"] != "Rayls (RLS)"]
    cols_per_row = 3

    for i in range(0, len(other_tokens), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(other_tokens):
                row = other_tokens.iloc[idx]
                project_name = row["Project"]
                current_price = row["Current Price ($)"]
                fdv = row["FDV ($)"]

                with col:
                    if current_price and not pd.isna(current_price):
                        st.markdown(f"""
                        <div class="token-card">
                            <div class="token-name">{project_name}</div>
                            <div class="token-price">${current_price:,.6f}</div>
                            <div class="token-fdv">FDV: {format_currency(fdv)}</div>
                            <div style="margin-top: 1rem;">
                                {get_change_badge(row["Change 24h (%)"])} 24h
                                {get_change_badge(row["Change 7d (%)"])} 7d
                                {get_change_badge(row["Change 30d (%)"])} 30d
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="token-card">
                            <div class="token-name">{project_name}</div>
                            <div class="token-price">N/A</div>
                            <div class="token-fdv">Price data unavailable</div>
                        </div>
                        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Price summary table with styling
    st.markdown('<div class="section-header">Price Summary Table</div>', unsafe_allow_html=True)

    price_df = df[["Project", "Current Price ($)", "FDV ($)", "Change 24h (%)", "Change 7d (%)", "Change 30d (%)"]].copy()
    price_df["Current Price ($)"] = price_df["Current Price ($)"].apply(
        lambda x: f"${x:,.6f}" if x and not pd.isna(x) else "N/A"
    )
    price_df["FDV ($)"] = price_df["FDV ($)"].apply(format_currency)
    price_df["Change 24h (%)"] = price_df["Change 24h (%)"].apply(format_percent_change)
    price_df["Change 7d (%)"] = price_df["Change 7d (%)"].apply(format_percent_change)
    price_df["Change 30d (%)"] = price_df["Change 30d (%)"].apply(format_percent_change)

    styled_price_df = price_df.style.map(color_percent_change, subset=["Change 24h (%)", "Change 7d (%)", "Change 30d (%)"])

    st.dataframe(
        styled_price_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Project": st.column_config.TextColumn("Token", width="medium"),
            "Current Price ($)": st.column_config.TextColumn("Price", width="small"),
            "FDV ($)": st.column_config.TextColumn("FDV", width="small"),
            "Change 24h (%)": st.column_config.TextColumn("24h", width="small"),
            "Change 7d (%)": st.column_config.TextColumn("7d", width="small"),
            "Change 30d (%)": st.column_config.TextColumn("30d", width="small"),
        }
    )

# Tab 3: Valuation Analysis
with tab3:
    st.markdown('<div class="section-header">FDV/Revenue vs Revenue Growth Analysis</div>', unsafe_allow_html=True)
    st.markdown("""
    This bubble chart helps identify valuation opportunities by comparing:
    - **X-axis**: Revenue growth rate (shows momentum)
    - **Y-axis**: FDV/Revenue multiple (shows valuation)
    - **Bubble size**: Market capitalization
    - **Quadrants**: Lower-right = "cheap growth" opportunities (high growth, low multiple)

    *Note: Rayls uses peer average growth rate since historical revenue data is not available.*
    """)

    # Select growth period first
    growth_period = st.radio(
        "Select Revenue Growth Period",
        ["30 Days", "90 Days"],
        horizontal=True
    )

    growth_col = "Revenue Growth 30d (%)" if growth_period == "30 Days" else "Revenue Growth 90d (%)"

    # Get peer data (without Rayls) for calculating average growth
    peers_df = df[
        (df["Project"] != "Rayls (RLS)") &
        (df[growth_col].notna()) &
        (df["Multiplier (FDV/Revenue)"].notna()) &
        (df["Market Cap ($)"].notna())
    ].copy()

    # Rayls hardcoded growth rates
    RAYLS_GROWTH_30D = 5.0  # 5% for 30 days
    RAYLS_GROWTH_90D = 2.0  # 2% for 90 days
    rayls_growth = RAYLS_GROWTH_30D if growth_period == "30 Days" else RAYLS_GROWTH_90D

    # Get Rayls data
    rayls_df = df[
        (df["Project"] == "Rayls (RLS)") &
        (df["Multiplier (FDV/Revenue)"].notna()) &
        (df["Market Cap ($)"].notna())
    ].copy()

    # Set Rayls growth to hardcoded values
    if len(rayls_df) > 0:
        rayls_df[growth_col] = rayls_growth
        rayls_df["Growth Source"] = "Estimated"

    # Add growth source to peers
    if len(peers_df) > 0:
        peers_df["Growth Source"] = "Actual"

    # Combine peers and Rayls
    chart_df = pd.concat([peers_df, rayls_df], ignore_index=True)

    if len(chart_df) > 0:
        # Show Rayls growth info
        st.info(f"**Rayls Revenue Growth ({growth_period}):** {rayls_growth:+.2f}% (estimated)")

        # Create bubble chart
        fig = px.scatter(
            chart_df,
            x=growth_col,
            y="Multiplier (FDV/Revenue)",
            size="Market Cap ($)",
            color="Project",
            hover_name="Project",
            hover_data={
                growth_col: ":.2f",
                "Multiplier (FDV/Revenue)": ":.2f",
                "Market Cap ($)": ":,.0f",
                "FDV ($)": ":,.0f",
                "Revenue 2025 ($)": ":,.0f",
                "Growth Source": True,
            },
            size_max=60,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )

            # Add quadrant lines at median values
        median_growth = chart_df[growth_col].median()
        median_multiplier = chart_df["Multiplier (FDV/Revenue)"].median()

        fig.add_hline(
            y=median_multiplier,
            line_dash="dash",
            line_color="gray",
            opacity=0.5,
            annotation_text=f"Median Multiplier: {median_multiplier:.1f}x",
            annotation_position="top right"
        )
        fig.add_vline(
            x=median_growth,
            line_dash="dash",
            line_color="gray",
            opacity=0.5,
            annotation_text=f"Median Growth: {median_growth:.1f}%",
            annotation_position="top right"
        )

        # Add quadrant labels
        fig.add_annotation(
            x=chart_df[growth_col].max() * 0.8,
            y=chart_df["Multiplier (FDV/Revenue)"].min() * 1.2,
            text="🎯 Cheap Growth",
            showarrow=False,
            font=dict(size=12, color="#16a34a"),
            bgcolor="rgba(22, 163, 74, 0.1)",
            borderpad=4
        )
        fig.add_annotation(
            x=chart_df[growth_col].min() * 0.8 if chart_df[growth_col].min() < 0 else chart_df[growth_col].min() * 1.2,
            y=chart_df["Multiplier (FDV/Revenue)"].max() * 0.9,
            text="⚠️ Overvalued",
            showarrow=False,
            font=dict(size=12, color="#dc2626"),
            bgcolor="rgba(220, 38, 38, 0.1)",
            borderpad=4
        )

        fig.update_layout(
            title=dict(
                text=f"Valuation vs Revenue Growth ({growth_period})",
                font=dict(size=20)
            ),
            xaxis_title=f"Revenue Growth ({growth_period}) %",
            yaxis_title="FDV/Revenue Multiple (x)",
            height=550,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(128,128,128,0.2)",
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="rgba(128,128,128,0.4)"
        )
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(128,128,128,0.2)"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Data table for the chart
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">Valuation Data</div>', unsafe_allow_html=True)

        valuation_df = chart_df[["Project", "Multiplier (FDV/Revenue)", growth_col, "Growth Source", "Market Cap ($)", "FDV ($)", "Revenue 2025 ($)"]].copy()
        valuation_df = valuation_df.sort_values(by=growth_col, ascending=False)

        # Format for display
        display_valuation_df = valuation_df.copy()
        display_valuation_df["Multiplier (FDV/Revenue)"] = valuation_df["Multiplier (FDV/Revenue)"].apply(format_multiplier)
        display_valuation_df[growth_col] = valuation_df[growth_col].apply(format_percent_change)
        display_valuation_df["Market Cap ($)"] = valuation_df["Market Cap ($)"].apply(format_currency)
        display_valuation_df["FDV ($)"] = valuation_df["FDV ($)"].apply(format_currency)
        display_valuation_df["Revenue 2025 ($)"] = valuation_df["Revenue 2025 ($)"].apply(format_currency)

        styled_valuation_df = display_valuation_df.style.map(
            color_percent_change,
            subset=[growth_col]
        )

        st.dataframe(
            styled_valuation_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Project": st.column_config.TextColumn("Project", width="medium"),
                "Multiplier (FDV/Revenue)": st.column_config.TextColumn("Multiplier", width="small"),
                growth_col: st.column_config.TextColumn("Growth", width="small"),
                "Growth Source": st.column_config.TextColumn("Source", width="small"),
                "Market Cap ($)": st.column_config.TextColumn("Market Cap", width="small"),
                "FDV ($)": st.column_config.TextColumn("FDV", width="small"),
                "Revenue 2025 ($)": st.column_config.TextColumn("Revenue '25", width="small"),
            }
        )

        # Insights section
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">Key Insights</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            # Best value (lowest multiplier with positive growth)
            positive_growth = chart_df[chart_df[growth_col] > 0]
            if len(positive_growth) > 0:
                best_value = positive_growth.loc[positive_growth["Multiplier (FDV/Revenue)"].idxmin()]
                st.success(f"""
                **Best Value Opportunity**

                **{best_value['Project']}**
                - Multiplier: {best_value['Multiplier (FDV/Revenue)']:.2f}x
                - Growth: {best_value[growth_col]:+.2f}%
                - Market Cap: {format_currency(best_value['Market Cap ($)'])}
                """)

        with col2:
            # Highest growth
            highest_growth = chart_df.loc[chart_df[growth_col].idxmax()]
            st.info(f"""
            **Highest Growth**

            **{highest_growth['Project']}**
            - Growth: {highest_growth[growth_col]:+.2f}%
            - Multiplier: {highest_growth['Multiplier (FDV/Revenue)']:.2f}x
            - Market Cap: {format_currency(highest_growth['Market Cap ($)'])}
            """)

        with col3:
            # Rayls positioning
            rayls_chart_row = chart_df[chart_df["Project"] == "Rayls (RLS)"]
            if len(rayls_chart_row) > 0:
                rayls_data = rayls_chart_row.iloc[0]
                rayls_mult = rayls_data["Multiplier (FDV/Revenue)"]
                median_mult = chart_df["Multiplier (FDV/Revenue)"].median()
                position = "below" if rayls_mult < median_mult else "above"
                position_emoji = "✅" if position == "below" else "⚠️"

                st.warning(f"""
                **Rayls Positioning**

                **{position_emoji} {position.title()} Median**
                - Multiplier: {rayls_mult:.2f}x
                - Median: {median_mult:.2f}x
                - Est. growth: {rayls_growth:+.1f}%
                """)

    else:
        st.warning("Insufficient data to generate the valuation chart. Revenue growth data is not available for the projects.")

# Tab 4: Price Performance
with tab4:
    st.markdown('<div class="section-header">Normalized Price Performance</div>', unsafe_allow_html=True)
    st.markdown("""
    Compare relative price performance across all tokens. All prices are normalized to **100** at the start date,
    allowing direct comparison regardless of absolute price levels.

    *Note: Rayls historical data may not be available due to API limitations.*
    """)

    # Time period selector
    time_period = st.radio(
        "Select Time Period",
        ["30 Days", "90 Days", "180 Days", "1 Year"],
        horizontal=True
    )

    days_map = {"30 Days": 30, "90 Days": 90, "180 Days": 180, "1 Year": 365}
    selected_days = days_map[time_period]

    # Token configurations for historical data
    token_configs = [
        {"name": "zkSync Era", "coingecko_id": "zksync"},
        {"name": "Plume Mainnet", "coingecko_id": "plume"},
        {"name": "Avalanche", "coingecko_id": "avalanche-2"},
        {"name": "Ondo Finance", "coingecko_id": "ondo-finance"},
        {"name": "Ondo Yield Assets", "coingecko_id": "ondo-us-dollar-yield"},
        {"name": "Polygon", "coingecko_id": "polygon-ecosystem-token"},
    ]

    @st.cache_data(ttl=600, show_spinner=False)  # Cache for 10 minutes
    def load_historical_prices(days: int):
        """Load historical price data for all tokens."""
        return price.getHistoricalPricesBatch(token_configs, days)

    with st.spinner(f"Loading {time_period} historical price data..."):
        historical_data = load_historical_prices(selected_days)

    if historical_data and len(historical_data) > 0:
        # Build normalized price dataframe
        all_series = []

        for token_name, prices in historical_data.items():
            if not prices or len(prices) < 2:
                continue

            # Extract timestamps and prices
            timestamps = [datetime.fromtimestamp(p[0] / 1000) for p in prices]
            price_values = [p[1] for p in prices]

            # Normalize to 100 at start
            start_price = price_values[0]
            if start_price and start_price > 0:
                normalized = [(p / start_price) * 100 for p in price_values]

                for i, (ts, norm_price) in enumerate(zip(timestamps, normalized)):
                    all_series.append({
                        "Date": ts,
                        "Normalized Price": norm_price,
                        "Token": token_name,
                        "Actual Price": price_values[i]
                    })

        if all_series:
            price_df = pd.DataFrame(all_series)

            # Create the line chart
            fig = px.line(
                price_df,
                x="Date",
                y="Normalized Price",
                color="Token",
                hover_data={"Actual Price": ":.6f", "Normalized Price": ":.2f"},
                color_discrete_sequence=px.colors.qualitative.Bold,
            )

            # Add reference line at 100
            fig.add_hline(
                y=100,
                line_dash="dash",
                line_color="gray",
                opacity=0.5,
                annotation_text="Starting Point (100)",
                annotation_position="bottom right"
            )

            fig.update_layout(
                title=dict(
                    text=f"Normalized Price Performance ({time_period})",
                    font=dict(size=20)
                ),
                xaxis_title="Date",
                yaxis_title="Normalized Price (Start = 100)",
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified"
            )

            fig.update_xaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
            )
            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
            )

            st.plotly_chart(fig, use_container_width=True)

            # Performance summary table
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">Performance Summary</div>', unsafe_allow_html=True)

            # Calculate performance metrics for each token
            perf_data = []
            for token_name, prices in historical_data.items():
                if not prices or len(prices) < 2:
                    continue

                start_price = prices[0][1]
                end_price = prices[-1][1]

                if start_price and start_price > 0:
                    total_return = ((end_price - start_price) / start_price) * 100

                    # Find max and min
                    price_values = [p[1] for p in prices]
                    max_price = max(price_values)
                    min_price = min(price_values)
                    max_drawdown = ((min_price - max_price) / max_price) * 100 if max_price > 0 else 0

                    perf_data.append({
                        "Token": token_name,
                        "Start Price": start_price,
                        "Current Price": end_price,
                        "Total Return (%)": total_return,
                        "Max Drawdown (%)": max_drawdown,
                        "Period High": max_price,
                        "Period Low": min_price,
                    })

            if perf_data:
                perf_df = pd.DataFrame(perf_data)
                perf_df = perf_df.sort_values("Total Return (%)", ascending=False)

                # Format for display
                display_perf_df = perf_df.copy()
                display_perf_df["Start Price"] = perf_df["Start Price"].apply(lambda x: f"${x:,.6f}")
                display_perf_df["Current Price"] = perf_df["Current Price"].apply(lambda x: f"${x:,.6f}")
                display_perf_df["Total Return (%)"] = perf_df["Total Return (%)"].apply(format_percent_change)
                display_perf_df["Max Drawdown (%)"] = perf_df["Max Drawdown (%)"].apply(lambda x: f"{x:.2f}%")
                display_perf_df["Period High"] = perf_df["Period High"].apply(lambda x: f"${x:,.6f}")
                display_perf_df["Period Low"] = perf_df["Period Low"].apply(lambda x: f"${x:,.6f}")

                styled_perf_df = display_perf_df.style.map(
                    color_percent_change,
                    subset=["Total Return (%)"]
                )

                st.dataframe(
                    styled_perf_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Token": st.column_config.TextColumn("Token", width="medium"),
                        "Start Price": st.column_config.TextColumn("Start", width="small"),
                        "Current Price": st.column_config.TextColumn("Current", width="small"),
                        "Total Return (%)": st.column_config.TextColumn("Return", width="small"),
                        "Max Drawdown (%)": st.column_config.TextColumn("Max DD", width="small"),
                        "Period High": st.column_config.TextColumn("High", width="small"),
                        "Period Low": st.column_config.TextColumn("Low", width="small"),
                    }
                )

                # Key insights
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="section-header">Key Insights</div>', unsafe_allow_html=True)

                col1, col2, col3 = st.columns(3)

                with col1:
                    best_performer = perf_df.iloc[0]
                    st.success(f"""
                    **Best Performer**

                    **{best_performer['Token']}**
                    - Return: {best_performer['Total Return (%)']:+.2f}%
                    - Current: ${best_performer['Current Price']:,.6f}
                    """)

                with col2:
                    worst_performer = perf_df.iloc[-1]
                    st.error(f"""
                    **Worst Performer**

                    **{worst_performer['Token']}**
                    - Return: {worst_performer['Total Return (%)']:+.2f}%
                    - Current: ${worst_performer['Current Price']:,.6f}
                    """)

                with col3:
                    avg_return = perf_df["Total Return (%)"].mean()
                    positive_count = len(perf_df[perf_df["Total Return (%)"] > 0])
                    total_count = len(perf_df)
                    st.info(f"""
                    **Market Overview**

                    - Avg Return: {avg_return:+.2f}%
                    - Winners: {positive_count}/{total_count}
                    - Period: {time_period}
                    """)

    else:
        st.warning("Unable to load historical price data. This may be due to API rate limits. Please try again later.")

# Footer with refresh button
st.markdown("<br>", unsafe_allow_html=True)
st.divider()

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.85rem; margin-top: 1rem;">
    Data refreshes automatically every 5 minutes • Prices from CoinGecko & CoinMarketCap
</div>
""", unsafe_allow_html=True)
