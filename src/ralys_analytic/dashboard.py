import logging
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from defillama_sdk import DefiLlama

logging.basicConfig(level=logging.INFO)

from metric import revenue
from metric import price
from metric import holders
from metric import analytics
from metric import etherscan
from metric import kraken_market
from metric import db_cache

try:
    db_cache.initialize_tables()
except Exception as e:
    logging.warning(f"DB cache initialization failed, will use API directly: {e}")

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📊 Project Comparison", "💹 Market Condition", "📈 Valuation Analysis", "👥 Token Holders", "💱 Token Analytics", "🏪 Market Analytics", "🐋 Whale Tracker"])


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    client = DefiLlama()

    # Metadata: (name, display_name, token_supply, circulating_token, coingecko_id, type, revenue_override)
    metadata = [
        ("zksync_era", "zkSync Era", 21_000_000_000, 8_620_000_000,"zksync", "protocol", None),
        ("plume_mainnet", "Plume Mainnet", 10_000_000_000, 4_800_000_000,"plume", "protocol", None),
        ("avalanche", "Avalanche", 715_740_000, 431_720_000,"avalanche-2", "protocol", None),
        ("ondo_finance", "Ondo Finance", 10_000_000_000,4_860_000_000, "ondo-finance", "protocol", None),
        ("ondo_yield_assets", "Ondo Yield Assets", 1_250_000_000, 628_940_000,"ondo-us-dollar-yield", "protocol", None),
        ("polygon", "Polygon", 10_000_000_000, 1_910_000_000, "polygon-ecosystem-token", "chain", None),
        ("chainlink", "Chainlink", 1_000_000_000, 626_000_000, "chainlink", "protocol", None),
        ("rayls", "Rayls (RLS)", 10_000_000_000, 1_500_000_000,"rls", "protocol", 2_000_000),
    ]

    def get_2025_revenue(revenue_data):
        annual_data = revenue.annualRevenue(revenue_data)
        for year, total in annual_data:
            if year == "2025":
                return total
        return None

    # Fetch CoinMarketCap prices for non-Rayls tokens
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
        _, display_name, token_supply,circulating_supply, coingecko_id, item_type, revenue_override = item

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

            results.append({
                "Project": display_name,
                "Current Price ($)": current_price,
                "Token Supply": token_supply,
                "FDV ($)": fdv,
                "Market Cap ($)": market_cap,
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
                "FDV ($)": None,
                "Market Cap ($)": None,
                "Revenue 2025 ($)": None,
                "Multiplier (FDV/Revenue)": None,
                "Revenue Growth 30d (%)": None,
                "Revenue Growth 90d (%)": None,
                "Change 24h (%)": None,
                "Change 7d (%)": None,
                "Change 30d (%)": None,
            })

    return pd.DataFrame(results)


# Track first load time for freshness indicator
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

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


def render_cache_notice(data_type: str, token_name: str = "Rayls (RLS)"):
    """Display a cache-age notice for Moralis-backed data (6-hour TTL)."""
    try:
        fetched_at_str = db_cache.get_cache_fetched_at(data_type, token_name)
        if fetched_at_str:
            fetched_dt = datetime.fromisoformat(fetched_at_str)
            # Normalise to naive UTC for arithmetic
            if fetched_dt.tzinfo is not None:
                fetched_dt = fetched_dt.replace(tzinfo=None)
            elapsed = datetime.utcnow() - fetched_dt
            total_sec = int(elapsed.total_seconds())
            hours, remainder = divmod(total_sec, 3600)
            minutes = remainder // 60
            if hours > 0:
                age_str = f"{hours}h {minutes}m ago"
            else:
                age_str = f"{minutes}m ago"
            fetched_label = fetched_dt.strftime("%Y-%m-%d %H:%M UTC")
            st.caption(
                f"ℹ️ This data is cached for up to **6 hours** and refreshed automatically. "
                f"Last fetched: **{age_str}** ({fetched_label})"
            )
        else:
            st.caption("ℹ️ This data is cached for up to **6 hours** and refreshed automatically. Fetch time unavailable.")
    except Exception:
        st.caption("ℹ️ This data is cached for up to **6 hours** and refreshed automatically.")


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
    display_cols = ["Project", "Current Price ($)", "Token Supply", "Market Cap ($)", "FDV ($)", "Revenue 2025 ($)",
                    "Multiplier (FDV/Revenue)", "Change 24h (%)", "Change 7d (%)", "Change 30d (%)"]
    display_df = df[display_cols].copy()
    display_df["Current Price ($)"] = df["Current Price ($)"].apply(lambda x: f"${x:,.6f}" if x and not pd.isna(x) else "N/A")
    display_df["Token Supply"] = df["Token Supply"].apply(format_supply)
    display_df["Market Cap ($)"] = df["Market Cap ($)"].apply(format_currency)
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
        width="stretch",
        hide_index=True,
        height=320,
        column_config={
            "Project": st.column_config.TextColumn("Project", width="medium"),
            "Current Price ($)": st.column_config.TextColumn("Price", width="small"),
            "Token Supply": st.column_config.TextColumn("Supply", width="small"),
            "Market Cap ($)": st.column_config.TextColumn("Mkt Cap", width="small"),
            "FDV ($)": st.column_config.TextColumn("FDV", width="small"),
            "Revenue 2025 ($)": st.column_config.TextColumn("Revenue '25", width="small"),
            "Multiplier (FDV/Revenue)": st.column_config.TextColumn("Multiplier", width="small"),
            "Change 24h (%)": st.column_config.TextColumn("24h", width="small"),
            "Change 7d (%)": st.column_config.TextColumn("7d", width="small"),
            "Change 30d (%)": st.column_config.TextColumn("30d", width="small"),
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
        width="stretch",
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
    # ==========================================
    # UNDERVALUATION ANALYSIS SECTION
    # ==========================================
    st.markdown('<div class="section-header">🎯 Rayls Undervaluation Analysis</div>', unsafe_allow_html=True)
    st.markdown("""
    This analysis compares Rayls' valuation multiple (FDV/Revenue) against peer protocols.
    A **lower multiple** indicates the token is **cheaper** relative to its revenue generation.
    """)

    # Prepare data for undervaluation chart
    valuation_data = df[df["Multiplier (FDV/Revenue)"].notna()].copy()
    valuation_data = valuation_data.sort_values("Multiplier (FDV/Revenue)", ascending=True)

    if len(valuation_data) > 0:
        # Calculate peer average (excluding Rayls)
        peers_only = valuation_data[valuation_data["Project"] != "Rayls (RLS)"]
        peer_avg_multiple = peers_only["Multiplier (FDV/Revenue)"].mean()
        peer_median_multiple = peers_only["Multiplier (FDV/Revenue)"].median()

        # Get Rayls data
        rayls_valuation = valuation_data[valuation_data["Project"] == "Rayls (RLS)"]

        if len(rayls_valuation) > 0:
            rayls_mult = rayls_valuation["Multiplier (FDV/Revenue)"].values[0]
            rayls_fdv = rayls_valuation["FDV ($)"].values[0]
            rayls_revenue = rayls_valuation["Revenue 2025 ($)"].values[0]

            # Calculate discount/premium vs peers
            discount_vs_avg = ((peer_avg_multiple - rayls_mult) / peer_avg_multiple) * 100
            discount_vs_median = ((peer_median_multiple - rayls_mult) / peer_median_multiple) * 100

            # Calculate implied fair value at peer multiples
            implied_fdv_at_avg = rayls_revenue * peer_avg_multiple if rayls_revenue else None
            implied_fdv_at_median = rayls_revenue * peer_median_multiple if rayls_revenue else None
            upside_at_avg = ((implied_fdv_at_avg - rayls_fdv) / rayls_fdv * 100) if implied_fdv_at_avg and rayls_fdv else None
            upside_at_median = ((implied_fdv_at_median - rayls_fdv) / rayls_fdv * 100) if implied_fdv_at_median and rayls_fdv else None

            # Key metrics row
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Rayls Multiple",
                    f"{rayls_mult:,.1f}x",
                    help="FDV divided by 2025 Revenue"
                )

            with col2:
                st.metric(
                    "Peer Average",
                    f"{peer_avg_multiple:,.1f}x",
                    delta=f"{discount_vs_avg:+.1f}% discount" if discount_vs_avg > 0 else f"{-discount_vs_avg:.1f}% premium",
                    delta_color="normal" if discount_vs_avg > 0 else "inverse"
                )

            with col3:
                st.metric(
                    "Implied FDV (at Avg)",
                    format_currency(implied_fdv_at_avg),
                    delta=f"{upside_at_avg:+.1f}% upside" if upside_at_avg else None,
                    delta_color="normal" if upside_at_avg and upside_at_avg > 0 else "off"
                )

            with col4:
                st.metric(
                    "Current FDV",
                    format_currency(rayls_fdv),
                    help="Current fully diluted valuation"
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # Horizontal bar chart - FDV/Revenue Multiple Comparison
            # Color Rayls differently
            valuation_data["Color"] = valuation_data["Project"].apply(
                lambda x: "Rayls (RLS)" if x == "Rayls (RLS)" else "Peers"
            )

            fig_bar = px.bar(
                valuation_data,
                y="Project",
                x="Multiplier (FDV/Revenue)",
                orientation="h",
                color="Color",
                color_discrete_map={"Rayls (RLS)": "#4299e1", "Peers": "#64748b"},
                hover_data={
                    "Multiplier (FDV/Revenue)": ":.2f",
                    "FDV ($)": ":,.0f",
                    "Revenue 2025 ($)": ":,.0f",
                    "Color": False
                },
            )

            # Add peer average line
            fig_bar.add_vline(
                x=peer_avg_multiple,
                line_dash="dash",
                line_color="#f97316",
                line_width=3,
                annotation_text=f"Peer Avg: {peer_avg_multiple:.1f}x",
                annotation_position="top",
                annotation_font_color="#f97316"
            )

            # Add peer median line
            fig_bar.add_vline(
                x=peer_median_multiple,
                line_dash="dot",
                line_color="#22c55e",
                line_width=2,
                annotation_text=f"Peer Median: {peer_median_multiple:.1f}x",
                annotation_position="bottom",
                annotation_font_color="#22c55e"
            )

            fig_bar.update_layout(
                title=dict(
                    text="FDV/Revenue Multiple Comparison (Lower = Cheaper)",
                    font=dict(size=18)
                ),
                xaxis_title="FDV/Revenue Multiple (x)",
                yaxis_title="",
                height=400,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    title=""
                ),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                bargap=0.3,
            )

            fig_bar.update_xaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
            )

            st.plotly_chart(fig_bar, width="stretch")

            # Bullet Chart - Rayls Multiple vs Peer Range
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 🎯 Bullet Chart: Rayls Valuation Position", unsafe_allow_html=True)
            st.markdown("Shows where each project's multiple sits within the valuation spectrum. **Blue diamond = Rayls**, gray circles = peers.")

            import plotly.graph_objects as go

            # Calculate peer statistics
            peer_min = peers_only["Multiplier (FDV/Revenue)"].min()
            peer_max = peers_only["Multiplier (FDV/Revenue)"].max()
            peer_25 = peers_only["Multiplier (FDV/Revenue)"].quantile(0.25)
            peer_75 = peers_only["Multiplier (FDV/Revenue)"].quantile(0.75)

            fig_bullet = go.Figure()

            # Background ranges (from worst to best for undervaluation)
            # Red zone: Above peer average (overvalued)
            fig_bullet.add_trace(go.Bar(
                x=[peer_max],
                y=["Valuation Multiple"],
                orientation='h',
                marker=dict(color='rgba(239, 68, 68, 0.3)'),
                name=f'Expensive Zone (>{peer_avg_multiple:.0f}x)',
                hoverinfo='skip',
                width=0.5
            ))

            # Yellow zone: Between median and average
            fig_bullet.add_trace(go.Bar(
                x=[peer_avg_multiple],
                y=["Valuation Multiple"],
                orientation='h',
                marker=dict(color='rgba(251, 191, 36, 0.4)'),
                name=f'Fair Value Zone ({peer_median_multiple:.0f}-{peer_avg_multiple:.0f}x)',
                hoverinfo='skip',
                width=0.5
            ))

            # Green zone: Below median (undervalued)
            fig_bullet.add_trace(go.Bar(
                x=[peer_median_multiple],
                y=["Valuation Multiple"],
                orientation='h',
                marker=dict(color='rgba(34, 197, 94, 0.4)'),
                name=f'Undervalued Zone (<{peer_median_multiple:.0f}x)',
                hoverinfo='skip',
                width=0.5
            ))

            # Add peer markers (circles)
            peer_colors = ['#94a3b8', '#78716c', '#a1a1aa', '#9ca3af', '#a3a3a3', '#8b8b8b']
            for idx, (_, peer_row) in enumerate(peers_only.iterrows()):
                peer_name = peer_row["Project"]
                peer_mult_val = peer_row["Multiplier (FDV/Revenue)"]
                peer_color = peer_colors[idx % len(peer_colors)]

                fig_bullet.add_trace(go.Scatter(
                    x=[peer_mult_val],
                    y=["Valuation Multiple"],
                    mode='markers+text',
                    marker=dict(
                        symbol='circle',
                        size=14,
                        color=peer_color,
                        line=dict(color='white', width=1)
                    ),
                    text=[peer_name.split()[0]],  # First word of name
                    textposition="bottom center",
                    textfont=dict(size=9, color=peer_color),
                    name=f'{peer_name} ({peer_mult_val:.1f}x)',
                    hovertemplate=f"<b>{peer_name}</b><br>Multiple: {peer_mult_val:.1f}x<extra></extra>",
                    showlegend=False
                ))

            # Rayls marker (diamond shape using scatter) - larger and highlighted
            fig_bullet.add_trace(go.Scatter(
                x=[rayls_mult],
                y=["Valuation Multiple"],
                mode='markers+text',
                marker=dict(
                    symbol='diamond',
                    size=24,
                    color='#3b82f6',
                    line=dict(color='white', width=3)
                ),
                text=[f"RLS: {rayls_mult:.1f}x"],
                textposition="top center",
                textfont=dict(size=14, color='#3b82f6', family='Arial Black'),
                name=f'⭐ Rayls ({rayls_mult:.1f}x)',
                hovertemplate=f"<b>Rayls (RLS)</b><br>Multiple: {rayls_mult:.1f}x<br>vs Peer Avg: {discount_vs_avg:+.1f}%<extra></extra>"
            ))

            # Add vertical lines for key reference points
            fig_bullet.add_vline(
                x=peer_avg_multiple,
                line_dash="dash",
                line_color="#f97316",
                line_width=2,
                annotation_text=f"Peer Avg: {peer_avg_multiple:.1f}x",
                annotation_position="top",
                annotation_font=dict(color="#f97316", size=11)
            )

            fig_bullet.add_vline(
                x=peer_median_multiple,
                line_dash="dot",
                line_color="#22c55e",
                line_width=2,
                annotation_text=f"Peer Median: {peer_median_multiple:.1f}x",
                annotation_position="bottom",
                annotation_font=dict(color="#22c55e", size=11)
            )

            fig_bullet.update_layout(
                title=dict(
                    text="Rayls Multiple vs Peer Range",
                    font=dict(size=18)
                ),
                xaxis_title="FDV/Revenue Multiple (x)",
                yaxis_title="",
                height=300,
                barmode='overlay',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.15,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=10)
                ),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    range=[0, peer_max * 1.1],
                    showgrid=True,
                    gridwidth=1,
                    gridcolor="rgba(128,128,128,0.2)",
                ),
                yaxis=dict(
                    showticklabels=False
                ),
                margin=dict(l=20, r=20, t=80, b=40)
            )

            st.plotly_chart(fig_bullet, width="stretch")

            # Add interpretation text
            if rayls_mult < peer_median_multiple:
                zone_text = "🟢 **Undervalued Zone** - Rayls trades below peer median"
            elif rayls_mult < peer_avg_multiple:
                zone_text = "🟡 **Fair Value Zone** - Rayls trades between median and average"
            else:
                zone_text = "🔴 **Premium Zone** - Rayls trades above peer average"

            st.markdown(f"""
            **Reading the Chart:**
            - 🟢 Green zone: Below peer median (undervalued)
            - 🟡 Yellow zone: Between median and average (fair value)
            - 🔴 Red zone: Above peer average (expensive)

            **Current Position:** {zone_text}
            """)

            # Discount/Premium Diverging Bar Chart
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 📉 Discount/Premium vs Peer Average", unsafe_allow_html=True)
            st.markdown("Shows how each project's valuation compares to the peer average. **Green bars (left) = trading at discount**, **Red bars (right) = trading at premium**.")

            # Calculate discount/premium for all projects
            diverging_data = valuation_data.copy()
            diverging_data["Discount/Premium (%)"] = diverging_data["Multiplier (FDV/Revenue)"].apply(
                lambda x: ((x - peer_avg_multiple) / peer_avg_multiple) * 100
            )
            diverging_data = diverging_data.sort_values("Discount/Premium (%)", ascending=True)

            # Create color based on discount (green) or premium (red)
            diverging_data["Bar Color"] = diverging_data["Discount/Premium (%)"].apply(
                lambda x: "#22c55e" if x < 0 else "#ef4444"
            )

            # Highlight Rayls
            diverging_data["Is Rayls"] = diverging_data["Project"].apply(
                lambda x: "⭐ " + x if x == "Rayls (RLS)" else x
            )

            fig_diverging = go.Figure()

            for _, row in diverging_data.iterrows():
                is_rayls = "Rayls" in row["Project"]
                bar_color = "#3b82f6" if is_rayls else row["Bar Color"]
                border_width = 3 if is_rayls else 1
                border_color = "#1d4ed8" if is_rayls else "white"

                fig_diverging.add_trace(go.Bar(
                    x=[row["Discount/Premium (%)"]],
                    y=[row["Is Rayls"]],
                    orientation='h',
                    marker=dict(
                        color=bar_color,
                        line=dict(color=border_color, width=border_width)
                    ),
                    text=[f"{row['Discount/Premium (%)']:+.1f}%"],
                    textposition="outside",
                    textfont=dict(
                        size=12 if is_rayls else 10,
                        color=bar_color,
                        family="Arial Black" if is_rayls else "Arial"
                    ),
                    hovertemplate=(
                        f"<b>{row['Project']}</b><br>"
                        f"Multiple: {row['Multiplier (FDV/Revenue)']:.1f}x<br>"
                        f"vs Peer Avg ({peer_avg_multiple:.1f}x): {row['Discount/Premium (%)']:+.1f}%<br>"
                        f"FDV: ${row['FDV ($)']:,.0f}<extra></extra>"
                    ),
                    showlegend=False
                ))

            # Add zero line
            fig_diverging.add_vline(
                x=0,
                line_color="#64748b",
                line_width=2,
                annotation_text="Peer Average",
                annotation_position="top",
                annotation_font=dict(color="#64748b", size=11)
            )

            fig_diverging.update_layout(
                title=dict(
                    text="Valuation Discount/Premium vs Peer Average Multiple",
                    font=dict(size=18)
                ),
                xaxis_title="Discount (←) / Premium (→) %",
                yaxis_title="",
                height=350,
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor="rgba(128,128,128,0.2)",
                    zeroline=True,
                    zerolinewidth=2,
                    zerolinecolor="#64748b",
                ),
                yaxis=dict(
                    showgrid=False,
                ),
                margin=dict(l=20, r=80, t=60, b=40)
            )

            st.plotly_chart(fig_diverging, width="stretch")

            # Summary for diverging chart
            rayls_discount = diverging_data[diverging_data["Project"] == "Rayls (RLS)"]["Discount/Premium (%)"].values[0]
            num_cheaper = len(diverging_data[diverging_data["Discount/Premium (%)"] < rayls_discount])
            num_total = len(diverging_data)

            if rayls_discount < 0:
                st.markdown(f"""
                **Key Insight:** Rayls trades at a **{abs(rayls_discount):.1f}% discount** to peer average.
                Only **{num_cheaper} out of {num_total}** projects trade at a larger discount.
                """)
            else:
                st.markdown(f"""
                **Key Insight:** Rayls trades at a **{rayls_discount:.1f}% premium** to peer average.
                """)

            # Implied Price Upside Chart
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 💰 Implied Price Upside", unsafe_allow_html=True)
            st.markdown("Compares current RLS price to implied fair prices at different peer valuation multiples.")

            # Get current Rayls price and token supply
            rayls_current_price = rayls_valuation["Current Price ($)"].values[0]
            rayls_token_supply = rayls_valuation["Token Supply"].values[0] if "Token Supply" in rayls_valuation.columns else 10_000_000_000

            # Calculate implied prices at different multiples
            if rayls_current_price and rayls_revenue and rayls_token_supply:
                # Implied FDV = Revenue * Multiple, Implied Price = Implied FDV / Token Supply
                implied_price_at_avg = (rayls_revenue * peer_avg_multiple) / rayls_token_supply
                implied_price_at_median = (rayls_revenue * peer_median_multiple) / rayls_token_supply
                implied_price_at_max = (rayls_revenue * peer_max) / rayls_token_supply

                # Calculate upside percentages
                upside_to_avg = ((implied_price_at_avg - rayls_current_price) / rayls_current_price) * 100
                upside_to_median = ((implied_price_at_median - rayls_current_price) / rayls_current_price) * 100
                upside_to_max = ((implied_price_at_max - rayls_current_price) / rayls_current_price) * 100

                # Create price comparison data
                price_scenarios = pd.DataFrame([
                    {
                        "Scenario": "Current Price",
                        "Price": rayls_current_price,
                        "Upside": 0,
                        "Type": "Current",
                        "Multiple": f"{rayls_mult:.1f}x"
                    },
                    {
                        "Scenario": "At Peer Median",
                        "Price": implied_price_at_median,
                        "Upside": upside_to_median,
                        "Type": "Implied",
                        "Multiple": f"{peer_median_multiple:.1f}x"
                    },
                    {
                        "Scenario": "At Peer Average",
                        "Price": implied_price_at_avg,
                        "Upside": upside_to_avg,
                        "Type": "Implied",
                        "Multiple": f"{peer_avg_multiple:.1f}x"
                    },
                    {
                        "Scenario": "At Peer Maximum",
                        "Price": implied_price_at_max,
                        "Upside": upside_to_max,
                        "Type": "Implied",
                        "Multiple": f"{peer_max:.1f}x"
                    },
                ])

                fig_price = go.Figure()

                # Add bars for each scenario
                colors = ["#3b82f6", "#22c55e", "#16a34a", "#15803d"]
                for idx, row in price_scenarios.iterrows():
                    fig_price.add_trace(go.Bar(
                        x=[row["Scenario"]],
                        y=[row["Price"]],
                        marker=dict(
                            color=colors[idx],
                            line=dict(color="white", width=2)
                        ),
                        text=[f"${row['Price']:.6f}"],
                        textposition="outside",
                        textfont=dict(size=11),
                        hovertemplate=(
                            f"<b>{row['Scenario']}</b><br>"
                            f"Price: ${row['Price']:.6f}<br>"
                            f"Multiple: {row['Multiple']}<br>"
                            f"Upside: {row['Upside']:+.1f}%<extra></extra>"
                        ),
                        showlegend=False
                    ))

                # Add upside percentage annotations
                for idx, row in price_scenarios.iterrows():
                    if row["Upside"] != 0:
                        fig_price.add_annotation(
                            x=row["Scenario"],
                            y=row["Price"],
                            text=f"+{row['Upside']:.0f}%",
                            showarrow=False,
                            yshift=35,
                            font=dict(size=12, color="#16a34a", family="Arial Black")
                        )

                fig_price.update_layout(
                    title=dict(
                        text="RLS Price: Current vs Implied Fair Value Scenarios",
                        font=dict(size=18)
                    ),
                    xaxis_title="",
                    yaxis_title="Price (USD)",
                    height=400,
                    showlegend=False,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(
                        showgrid=True,
                        gridwidth=1,
                        gridcolor="rgba(128,128,128,0.2)",
                        tickformat=".6f"
                    ),
                    margin=dict(l=20, r=20, t=60, b=40)
                )

                st.plotly_chart(fig_price, width="stretch")

                # Price target summary table
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Current Price",
                        f"${rayls_current_price:.6f}",
                        help=f"At {rayls_mult:.1f}x multiple"
                    )

                with col2:
                    st.metric(
                        "Target (Peer Avg)",
                        f"${implied_price_at_avg:.6f}",
                        delta=f"+{upside_to_avg:.1f}% upside",
                        delta_color="normal"
                    )

                with col3:
                    st.metric(
                        "Target (Peer Max)",
                        f"${implied_price_at_max:.6f}",
                        delta=f"+{upside_to_max:.1f}% upside",
                        delta_color="normal"
                    )

                st.markdown(f"""
                **Price Implications:**
                - If RLS traded at **peer average multiple ({peer_avg_multiple:.1f}x)**, price would be **${implied_price_at_avg:.6f}** (+{upside_to_avg:.0f}% upside)
                - If RLS traded at **peer maximum multiple ({peer_max:.1f}x)**, price would be **${implied_price_at_max:.6f}** (+{upside_to_max:.0f}% upside)
                """)

            # Scatter Plot: FDV vs Revenue with Trend Line
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 📈 FDV vs Revenue: Fair Value Line", unsafe_allow_html=True)
            st.markdown("Projects **below** the trend line are undervalued (lower FDV for their revenue). Projects **above** are overvalued.")

            import numpy as np

            # Prepare scatter data - need both FDV and Revenue
            scatter_data = valuation_data[
                (valuation_data["FDV ($)"].notna()) &
                (valuation_data["Revenue 2025 ($)"].notna()) &
                (valuation_data["Revenue 2025 ($)"] > 0)
            ].copy()

            if len(scatter_data) >= 2:
                # Helper function to format values in M/B
                def format_val_short(val):
                    if val >= 1e9:
                        return f"${val/1e9:.2f}B"
                    elif val >= 1e6:
                        return f"${val/1e6:.2f}M"
                    elif val >= 1e3:
                        return f"${val/1e3:.2f}K"
                    else:
                        return f"${val:,.0f}"

                # Calculate trend line using linear regression
                x_rev = scatter_data["Revenue 2025 ($)"].values
                y_fdv = scatter_data["FDV ($)"].values

                # Log transform for better fit (common in financial data)
                log_x = np.log10(x_rev)
                log_y = np.log10(y_fdv)

                # Linear regression on log-transformed data
                slope, intercept = np.polyfit(log_x, log_y, 1)

                # Generate trend line points
                x_line = np.linspace(x_rev.min() * 0.8, x_rev.max() * 1.2, 100)
                y_line = 10 ** (slope * np.log10(x_line) + intercept)

                # Calculate distance from trend line for each point (for coloring)
                scatter_data["Expected FDV"] = 10 ** (slope * np.log10(scatter_data["Revenue 2025 ($)"]) + intercept)
                scatter_data["Deviation (%)"] = ((scatter_data["FDV ($)"] - scatter_data["Expected FDV"]) / scatter_data["Expected FDV"]) * 100

                # Create scatter plot
                fig_scatter = go.Figure()

                # Add trend line first (so it's behind points)
                fig_scatter.add_trace(go.Scatter(
                    x=x_line,
                    y=y_line,
                    mode='lines',
                    name='Fair Value Line',
                    line=dict(color='#f97316', width=3, dash='dash'),
                    hoverinfo='skip'
                ))

                # Add shaded area below trend line (undervalued zone)
                fig_scatter.add_trace(go.Scatter(
                    x=np.concatenate([x_line, x_line[::-1]]),
                    y=np.concatenate([y_line, np.zeros_like(y_line)]),
                    fill='toself',
                    fillcolor='rgba(34, 197, 94, 0.1)',
                    line=dict(color='rgba(0,0,0,0)'),
                    name='Undervalued Zone',
                    hoverinfo='skip'
                ))

                # Add peer points
                peers_scatter = scatter_data[scatter_data["Project"] != "Rayls (RLS)"]
                for _, row in peers_scatter.iterrows():
                    is_undervalued = row["Deviation (%)"] < 0
                    point_color = "#22c55e" if is_undervalued else "#ef4444"

                    fig_scatter.add_trace(go.Scatter(
                        x=[row["Revenue 2025 ($)"]],
                        y=[row["FDV ($)"]],
                        mode='markers+text',
                        marker=dict(
                            size=12,
                            color=point_color,
                            line=dict(color='white', width=1),
                            symbol='circle'
                        ),
                        text=[row["Project"].split()[0]],
                        textposition="top center",
                        textfont=dict(size=9, color=point_color),
                        name=row["Project"],
                        hovertemplate=(
                            f"<b>{row['Project']}</b><br>"
                            f"Revenue: {format_val_short(row['Revenue 2025 ($)'])}<br>"
                            f"FDV: {format_val_short(row['FDV ($)'])}<br>"
                            f"vs Fair Value: {row['Deviation (%)']:+.1f}%<extra></extra>"
                        ),
                        showlegend=False
                    ))

                # Add Rayls point (highlighted)
                rayls_scatter = scatter_data[scatter_data["Project"] == "Rayls (RLS)"]
                if len(rayls_scatter) > 0:
                    rayls_row = rayls_scatter.iloc[0]
                    rayls_deviation = rayls_row["Deviation (%)"]

                    fig_scatter.add_trace(go.Scatter(
                        x=[rayls_row["Revenue 2025 ($)"]],
                        y=[rayls_row["FDV ($)"]],
                        mode='markers+text',
                        marker=dict(
                            size=20,
                            color='#3b82f6',
                            line=dict(color='white', width=3),
                            symbol='diamond'
                        ),
                        text=["⭐ RLS"],
                        textposition="top center",
                        textfont=dict(size=12, color='#3b82f6', family='Arial Black'),
                        name=f"Rayls ({rayls_deviation:+.1f}% vs fair value)",
                        hovertemplate=(
                            f"<b>Rayls (RLS)</b><br>"
                            f"Revenue: {format_val_short(rayls_row['Revenue 2025 ($)'])}<br>"
                            f"FDV: {format_val_short(rayls_row['FDV ($)'])}<br>"
                            f"vs Fair Value: {rayls_deviation:+.1f}%<br>"
                            f"<b>{'UNDERVALUED' if rayls_deviation < 0 else 'OVERVALUED'}</b><extra></extra>"
                        ),
                    ))

                # Custom tick values for revenue (X-axis) in millions
                x_tickvals = [1e6, 5e6, 10e6, 50e6, 100e6, 500e6, 1e9]
                x_ticktext = ["$1M", "$5M", "$10M", "$50M", "$100M", "$500M", "$1B"]

                # Custom tick values for FDV (Y-axis) in billions
                y_tickvals = [100e6, 500e6, 1e9, 5e9, 10e9, 50e9, 100e9, 500e9]
                y_ticktext = ["$100M", "$500M", "$1B", "$5B", "$10B", "$50B", "$100B", "$500B"]

                fig_scatter.update_layout(
                    title=dict(
                        text="FDV vs Revenue: Who's Under/Overvalued?",
                        font=dict(size=18)
                    ),
                    xaxis_title="Revenue 2025",
                    yaxis_title="Fully Diluted Valuation (FDV)",
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
                    xaxis=dict(
                        showgrid=True,
                        gridwidth=1,
                        gridcolor="rgba(128,128,128,0.2)",
                        type="log",
                        tickvals=x_tickvals,
                        ticktext=x_ticktext,
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridwidth=1,
                        gridcolor="rgba(128,128,128,0.2)",
                        type="log",
                        tickvals=y_tickvals,
                        ticktext=y_ticktext,
                    ),
                )

                st.plotly_chart(fig_scatter, width="stretch")

                # Insight based on Rayls position
                if len(rayls_scatter) > 0:
                    rayls_deviation = rayls_scatter.iloc[0]["Deviation (%)"]
                    if rayls_deviation < 0:
                        st.success(f"""
                        **Chart Insight:** Rayls (blue diamond) sits **below** the fair value line, trading at **{abs(rayls_deviation):.1f}% below**
                        where it should be based on its revenue. This visual confirms RLS is undervalued relative to the peer group's
                        revenue-to-FDV relationship.
                        """)
                    else:
                        st.info(f"""
                        **Chart Insight:** Rayls (blue diamond) sits **above** the fair value line, trading at **{rayls_deviation:.1f}% above**
                        the expected valuation based on its revenue.
                        """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # ORIGINAL BUBBLE CHART SECTION
    # ==========================================
    st.markdown('<div class="section-header">FDV/Revenue vs Revenue Growth Analysis</div>', unsafe_allow_html=True)
    st.markdown("""
    This bubble chart helps identify valuation opportunities by comparing:
    - **X-axis**: Revenue growth rate (shows momentum)
    - **Y-axis**: FDV/Revenue multiple (shows valuation)
    - **Bubble size**: Market capitalization
    - **Quadrants**: Lower-right = "cheap growth" opportunities (high growth, low multiple)

    *Note: Rayls historical revenue data is not available. Use the slider below to model different growth scenarios.*
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

    # Rayls growth rate slider (no historical data available)
    if growth_period == "30 Days":
        rayls_growth = st.slider(
            "Rayls Estimated Revenue Growth (30 Days) %",
            min_value=-50.0,
            max_value=100.0,
            value=5.0,
            step=0.5,
            format="%.1f%%",
            key="rayls_growth_30d",
            help="Adjust Rayls' estimated 30-day revenue growth rate to model different scenarios."
        )
    else:
        rayls_growth = st.slider(
            "Rayls Estimated Revenue Growth (90 Days) %",
            min_value=-50.0,
            max_value=100.0,
            value=2.0,
            step=0.5,
            format="%.1f%%",
            key="rayls_growth_90d",
            help="Adjust Rayls' estimated 90-day revenue growth rate to model different scenarios."
        )

    # Get Rayls data
    rayls_df = df[
        (df["Project"] == "Rayls (RLS)") &
        (df["Multiplier (FDV/Revenue)"].notna()) &
        (df["Market Cap ($)"].notna())
    ].copy()

    # Set Rayls growth to user-specified value
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
        st.info(f"**Rayls Revenue Growth ({growth_period}):** {rayls_growth:+.2f}% (user-defined scenario)")

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

        st.plotly_chart(fig, width="stretch")

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
            width="stretch",
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

# Tab 4: Token Holders
with tab4:
    st.markdown('<div class="section-header">Token Holder Analytics</div>', unsafe_allow_html=True)
    st.markdown("""
    Track token holder metrics across Ethereum mainnet. Data powered by **Moralis API**.
    """)

    @st.cache_data(ttl=600)  # Cache for 10 minutes
    def load_holders_data():
        """Load token holder data (DB cache -> Moralis API fallback)."""
        return holders.get_all_token_holders_data_cached()

    with st.spinner("Loading token holder data from Moralis..."):
        holders_data = load_holders_data()

    render_cache_notice("holders")

    if holders_data:
        # Rayls highlight section
        rayls_holders = holders_data.get("Rayls (RLS)", {})

        st.markdown('<div class="section-header">Rayls (RLS) Holder Overview</div>', unsafe_allow_html=True)

        # Get holder change data
        holder_change = rayls_holders.get("holder_change", {})

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            holder_count = rayls_holders.get("holder_count")
            change_24h = holder_change.get("24h", {}) if holder_change else {}
            st.metric(
                label="Total Holders",
                value=f"{holder_count:,}" if holder_count else "N/A",
                delta=f"{change_24h.get('changePercent', 0):+.2f}% (24h)" if change_24h.get('changePercent') else None
            )

        with col2:
            change_3d = holder_change.get("3d", {}) if holder_change else {}
            st.metric(
                label="3 Day Change",
                value=f"{change_3d.get('change', 0):+,}" if change_3d.get('change') else "0",
                delta=f"{change_3d.get('changePercent', 0):+.2f}%" if change_3d.get('changePercent') else None
            )

        with col3:
            change_7d = holder_change.get("7d", {}) if holder_change else {}
            st.metric(
                label="7 Day Change",
                value=f"{change_7d.get('change', 0):+,}" if change_7d.get('change') else "0",
                delta=f"{change_7d.get('changePercent', 0):+.2f}%" if change_7d.get('changePercent') else None
            )

        with col4:
            change_30d = holder_change.get("30d", {}) if holder_change else {}
            st.metric(
                label="30 Day Change",
                value=f"{change_30d.get('change', 0):+,}" if change_30d.get('change') else "0",
                delta=f"{change_30d.get('changePercent', 0):+.2f}%" if change_30d.get('changePercent') else None
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Holder Distribution Section (Whales, Sharks, etc.)
        holder_distribution = rayls_holders.get("holder_distribution", {})

        if holder_distribution:
            st.markdown('<div class="section-header">Holder Distribution by Type</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                # Create distribution data
                dist_data = pd.DataFrame([
                    {"Type": "Whales (>1%)", "Count": holder_distribution.get("whales", 0), "Color": "#ef4444"},
                    {"Type": "Sharks (0.1-1%)", "Count": holder_distribution.get("sharks", 0), "Color": "#f97316"},
                    {"Type": "Dolphins (0.01-0.1%)", "Count": holder_distribution.get("dolphins", 0), "Color": "#eab308"},
                    {"Type": "Fish (0.001-0.01%)", "Count": holder_distribution.get("fish", 0), "Color": "#22c55e"},
                    {"Type": "Octopus (0.0001-0.001%)", "Count": holder_distribution.get("octopus", 0), "Color": "#06b6d4"},
                    {"Type": "Crabs (0.00001-0.0001%)", "Count": holder_distribution.get("crabs", 0), "Color": "#3b82f6"},
                    {"Type": "Shrimps (<0.00001%)", "Count": holder_distribution.get("shrimps", 0), "Color": "#8b5cf6"},
                ])

                fig_dist = px.bar(
                    dist_data,
                    x="Type",
                    y="Count",
                    color="Type",
                    color_discrete_sequence=["#ef4444", "#f97316", "#eab308", "#22c55e", "#06b6d4", "#3b82f6", "#8b5cf6"],
                    text="Count",
                )

                fig_dist.update_traces(textposition="outside", showlegend=False)

                fig_dist.update_layout(
                    title=dict(text="Holder Types Distribution", font=dict(size=16)),
                    xaxis_title="",
                    yaxis_title="Number of Holders",
                    height=400,
                    showlegend=False,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(tickangle=-45),
                )

                fig_dist.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")

                st.plotly_chart(fig_dist, width="stretch")

            with col2:
                # Pie chart for holder distribution (excluding shrimps for better visibility)
                dist_pie = dist_data[dist_data["Type"] != "Shrimps (<0.00001%)"].copy()

                fig_pie_dist = px.pie(
                    dist_pie,
                    values="Count",
                    names="Type",
                    color_discrete_sequence=["#ef4444", "#f97316", "#eab308", "#22c55e", "#06b6d4", "#3b82f6"],
                    hole=0.4,
                )

                fig_pie_dist.update_traces(textposition="outside", textinfo="percent+label", textfont_size=10)

                fig_pie_dist.update_layout(
                    title=dict(text="Distribution (excl. Shrimps)", font=dict(size=16)),
                    height=400,
                    showlegend=False,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )

                st.plotly_chart(fig_pie_dist, width="stretch")

            # Distribution metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Whales", f"{holder_distribution.get('whales', 0):,}", help="Holders with >1% supply")
            with col2:
                st.metric("Sharks", f"{holder_distribution.get('sharks', 0):,}", help="Holders with 0.1-1% supply")
            with col3:
                st.metric("Dolphins", f"{holder_distribution.get('dolphins', 0):,}", help="Holders with 0.01-0.1% supply")
            with col4:
                st.metric("Shrimps", f"{holder_distribution.get('shrimps', 0):,}", help="Small holders <0.00001%")

        st.markdown("<br>", unsafe_allow_html=True)

        # Holder Supply Concentration
        holder_supply = rayls_holders.get("holder_supply", {})

        if holder_supply:
            st.markdown('<div class="section-header">Supply Concentration</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                # Bar chart for concentration
                conc_data = pd.DataFrame([
                    {"Group": "Top 10", "Supply %": float(holder_supply.get("top10", {}).get("supplyPercent", 0))},
                    {"Group": "Top 25", "Supply %": float(holder_supply.get("top25", {}).get("supplyPercent", 0))},
                    {"Group": "Top 50", "Supply %": float(holder_supply.get("top50", {}).get("supplyPercent", 0))},
                    {"Group": "Top 100", "Supply %": float(holder_supply.get("top100", {}).get("supplyPercent", 0))},
                    {"Group": "Top 250", "Supply %": float(holder_supply.get("top250", {}).get("supplyPercent", 0))},
                ])

                fig_conc = px.bar(
                    conc_data,
                    x="Group",
                    y="Supply %",
                    color="Supply %",
                    color_continuous_scale="Blues",
                    text=conc_data["Supply %"].apply(lambda x: f"{x:.0f}%"),
                )

                fig_conc.update_traces(textposition="outside")

                fig_conc.update_layout(
                    title=dict(text="Supply Held by Top Holders", font=dict(size=16)),
                    xaxis_title="",
                    yaxis_title="% of Total Supply",
                    height=350,
                    showlegend=False,
                    coloraxis_showscale=False,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )

                fig_conc.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)", range=[0, 110])

                st.plotly_chart(fig_conc, width="stretch")

            with col2:
                # Key concentration metrics
                st.markdown("#### Concentration Metrics")

                top10_pct = float(holder_supply.get("top10", {}).get("supplyPercent", 0))
                top10_supply = float(holder_supply.get("top10", {}).get("supply", 0))

                st.metric("Top 10 Holders", f"{top10_pct:.0f}%", help=f"Supply: {top10_supply:,.0f} RLS")

                top25_pct = float(holder_supply.get("top25", {}).get("supplyPercent", 0))
                st.metric("Top 25 Holders", f"{top25_pct:.0f}%")

                top100_pct = float(holder_supply.get("top100", {}).get("supplyPercent", 0))
                st.metric("Top 100 Holders", f"{top100_pct:.0f}%")

                # Concentration assessment
                if top10_pct >= 80:
                    st.error("Very High Concentration - Top 10 hold >80%")
                elif top10_pct >= 60:
                    st.warning("High Concentration - Top 10 hold >60%")
                elif top10_pct >= 40:
                    st.info("Moderate Concentration - Top 10 hold >40%")
                else:
                    st.success("Well Distributed - Top 10 hold <40%")

        st.markdown("<br>", unsafe_allow_html=True)

        # All tokens holder comparison
        st.markdown('<div class="section-header">Token Holder Comparison</div>', unsafe_allow_html=True)

        # Build comparison dataframe
        holder_comparison = []
        for token_name, data in holders_data.items():
            holder_count = data.get("holder_count")
            h_change = data.get("holder_change", {})

            holder_comparison.append({
                "Token": token_name,
                "Holders": holder_count if holder_count else None,
                "24h Change": h_change.get("24h", {}).get("change", 0) if h_change else 0,
                "24h %": h_change.get("24h", {}).get("changePercent", 0) if h_change else 0,
                "7d Change": h_change.get("7d", {}).get("change", 0) if h_change else 0,
                "7d %": h_change.get("7d", {}).get("changePercent", 0) if h_change else 0,
                "30d Change": h_change.get("30d", {}).get("change", 0) if h_change else 0,
                "30d %": h_change.get("30d", {}).get("changePercent", 0) if h_change else 0,
                "Contract": data.get("contract_address", ""),
            })

        holder_df = pd.DataFrame(holder_comparison)

        # Sort by holder count descending
        holder_df = holder_df.sort_values("Holders", ascending=False, na_position="last")

        # Create bar chart for holder comparison
        chart_data = holder_df[holder_df["Holders"].notna()].copy()

        if len(chart_data) > 0:
            # Color Rayls differently
            chart_data["Color"] = chart_data["Token"].apply(
                lambda x: "Rayls (RLS)" if x == "Rayls (RLS)" else "Other Tokens"
            )

            fig_holders = px.bar(
                chart_data,
                x="Token",
                y="Holders",
                color="Color",
                color_discrete_map={"Rayls (RLS)": "#4299e1", "Other Tokens": "#64748b"},
                text=chart_data["Holders"].apply(lambda x: f"{x:,.0f}" if x else "N/A"),
            )

            fig_holders.update_traces(textposition="outside")

            fig_holders.update_layout(
                title=dict(
                    text="Token Holder Count Comparison",
                    font=dict(size=18)
                ),
                xaxis_title="",
                yaxis_title="Number of Holders",
                height=400,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    title=""
                ),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )

            fig_holders.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
            )

            st.plotly_chart(fig_holders, width="stretch")

        st.markdown("<br>", unsafe_allow_html=True)

        # 100% Stacked Bar (Normalized Holder Distribution)
        st.markdown('<div class="section-header">Holder Distribution Comparison</div>', unsafe_allow_html=True)
        st.markdown("""
        Compare the proportional breakdown of holder categories across tokens.
        Each bar shows the **percentage of holders** in each category, making it easy to compare distribution shapes.
        """)

        # Build normalized distribution data
        distribution_data = []
        category_colors = {
            "Whales (>1%)": "#ef4444",
            "Sharks (0.1-1%)": "#f97316",
            "Dolphins (0.01-0.1%)": "#eab308",
            "Fish (0.001-0.01%)": "#22c55e",
            "Octopus": "#06b6d4",
            "Crabs": "#3b82f6",
            "Shrimps": "#8b5cf6",
        }

        for token_name, data in holders_data.items():
            dist = data.get("holder_distribution", {})
            if dist:
                whales = dist.get("whales", 0)
                sharks = dist.get("sharks", 0)
                dolphins = dist.get("dolphins", 0)
                fish = dist.get("fish", 0)
                octopus = dist.get("octopus", 0)
                crabs = dist.get("crabs", 0)
                shrimps = dist.get("shrimps", 0)

                total = whales + sharks + dolphins + fish + octopus + crabs + shrimps
                if total > 0:
                    distribution_data.extend([
                        {"Token": token_name, "Category": "Whales (>1%)", "Percentage": (whales / total) * 100, "Order": 1},
                        {"Token": token_name, "Category": "Sharks (0.1-1%)", "Percentage": (sharks / total) * 100, "Order": 2},
                        {"Token": token_name, "Category": "Dolphins (0.01-0.1%)", "Percentage": (dolphins / total) * 100, "Order": 3},
                        {"Token": token_name, "Category": "Fish (0.001-0.01%)", "Percentage": (fish / total) * 100, "Order": 4},
                        {"Token": token_name, "Category": "Octopus", "Percentage": (octopus / total) * 100, "Order": 5},
                        {"Token": token_name, "Category": "Crabs", "Percentage": (crabs / total) * 100, "Order": 6},
                        {"Token": token_name, "Category": "Shrimps", "Percentage": (shrimps / total) * 100, "Order": 7},
                    ])

        if distribution_data:
            dist_df = pd.DataFrame(distribution_data)
            dist_df = dist_df.sort_values(["Token", "Order"])

            fig_stacked = px.bar(
                dist_df,
                y="Token",
                x="Percentage",
                color="Category",
                orientation="h",
                color_discrete_map=category_colors,
                category_orders={"Category": list(category_colors.keys())},
                text=dist_df["Percentage"].apply(lambda x: f"{x:.1f}%" if x >= 5 else ""),
            )

            fig_stacked.update_traces(
                textposition="inside",
                textfont=dict(color="white", size=11),
            )

            fig_stacked.update_layout(
                title=dict(
                    text="Normalized Holder Distribution by Token",
                    font=dict(size=18),
                ),
                xaxis_title="Percentage of Holders",
                yaxis_title="",
                xaxis=dict(
                    ticksuffix="%",
                    range=[0, 100],
                    showgrid=True,
                    gridcolor="rgba(128,128,128,0.2)",
                ),
                height=350,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.4,
                    xanchor="center",
                    x=0.5,
                    title="",
                ),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                bargap=0.3,
            )

            st.plotly_chart(fig_stacked, width="stretch")

        st.markdown("<br>", unsafe_allow_html=True)

        # Holder Growth Rate Comparison (Heatmap)
        st.markdown('<div class="section-header">Holder Growth Rate Comparison</div>', unsafe_allow_html=True)
        st.markdown("""
        Compare holder growth rates across different time periods. **Green indicates growth**, **red indicates decline**.
        Identifies which tokens are gaining or losing holders fastest.
        """)

        # Build growth rate data for heatmap
        growth_data = []
        for token_name, data in holders_data.items():
            h_change = data.get("holder_change", {})
            if h_change:
                growth_data.append({
                    "Token": token_name,
                    "24h": h_change.get("24h", {}).get("changePercent", 0) if h_change.get("24h") else 0,
                    "7d": h_change.get("7d", {}).get("changePercent", 0) if h_change.get("7d") else 0,
                    "30d": h_change.get("30d", {}).get("changePercent", 0) if h_change.get("30d") else 0,
                })

        if growth_data:
            growth_df = pd.DataFrame(growth_data)
            growth_df = growth_df.set_index("Token")

            # Create heatmap using plotly
            import plotly.graph_objects as go

            fig_heatmap = go.Figure(data=go.Heatmap(
                z=growth_df.values,
                x=growth_df.columns,
                y=growth_df.index,
                colorscale=[
                    [0, "#ef4444"],      # Red for negative
                    [0.5, "#fafafa"],    # White for zero
                    [1, "#22c55e"],      # Green for positive
                ],
                zmid=0,
                text=[[f"{val:+.2f}%" for val in row] for row in growth_df.values],
                texttemplate="%{text}",
                textfont=dict(size=14, color="#1f2937"),
                hovertemplate="Token: %{y}<br>Period: %{x}<br>Change: %{text}<extra></extra>",
            ))

            fig_heatmap.update_layout(
                title=dict(
                    text="Holder Change % by Time Period",
                    font=dict(size=18),
                ),
                xaxis_title="Time Period",
                yaxis_title="",
                height=300,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    side="bottom",
                    tickfont=dict(size=13),
                ),
                yaxis=dict(
                    tickfont=dict(size=12),
                    autorange="reversed",
                ),
            )

            st.plotly_chart(fig_heatmap, width="stretch")

        st.markdown("<br>", unsafe_allow_html=True)

        # Holder data table
        st.markdown('<div class="section-header">Holder Data Summary</div>', unsafe_allow_html=True)

        display_holder_df = holder_df[holder_df["Token"] != "Avalanche"].copy()
        display_holder_df["Holders"] = display_holder_df["Holders"].apply(
            lambda x: f"{x:,.0f}" if x and not pd.isna(x) else "N/A"
        )
        display_holder_df["24h"] = display_holder_df.apply(
            lambda row: f"{row['24h Change']:+,} ({row['24h %']:+.2f}%)" if row['24h Change'] else "0 (0%)", axis=1
        )
        display_holder_df["7d"] = display_holder_df.apply(
            lambda row: f"{row['7d Change']:+,} ({row['7d %']:+.2f}%)" if row['7d Change'] else "0 (0%)", axis=1
        )
        display_holder_df["30d"] = display_holder_df.apply(
            lambda row: f"{row['30d Change']:+,} ({row['30d %']:+.2f}%)" if row['30d Change'] else "0 (0%)", axis=1
        )
        display_holder_df["Contract"] = display_holder_df["Contract"].apply(
            lambda x: x[:10] + "..." + x[-6:] if x else "N/A"
        )

        st.dataframe(
            display_holder_df[["Token", "Holders", "24h", "7d", "30d", "Contract"]],
            width="stretch",
            hide_index=True,
            column_config={
                "Token": st.column_config.TextColumn("Token", width="medium"),
                "Holders": st.column_config.TextColumn("Holders", width="small"),
                "24h": st.column_config.TextColumn("24h Change", width="medium"),
                "7d": st.column_config.TextColumn("7d Change", width="medium"),
                "30d": st.column_config.TextColumn("30d Change", width="medium"),
                "Contract": st.column_config.TextColumn("Contract", width="medium"),
            }
        )


    else:
        st.warning("Unable to load token holder data. Please check your Moralis API key.")

with tab5:
    st.markdown('<div class="section-header">Token Trading Analytics</div>', unsafe_allow_html=True)
    st.markdown("""
    Track token trading metrics including buy/sell volume, unique wallets, and price changes. Data powered by **Moralis API**.
    """)

    @st.cache_data(ttl=600)  # Cache for 10 minutes
    def load_analytics_data():
        """Load token analytics data (DB cache -> Moralis API fallback)."""
        return analytics.get_all_token_analytics_cached()

    with st.spinner("Loading token analytics data from Moralis..."):
        analytics_data = load_analytics_data()

    render_cache_notice("analytics")

    if analytics_data:
        # Rayls highlight section
        rayls_analytics = analytics_data.get("Rayls (RLS)", {})

        st.markdown('<div class="section-header">Rayls (RLS) Trading Overview (Ethereum Network)</div>', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            usd_price = rayls_analytics.get("usd_price")
            price_change = rayls_analytics.get("price_percent_change", {})
            st.metric(
                label="USD Price",
                value=f"${float(usd_price):.6f}" if usd_price else "N/A",
                delta=f"{price_change.get('24h', 0):+.2f}% (24h)" if price_change.get('24h') else None
            )

        with col2:
            liquidity = rayls_analytics.get("total_liquidity_usd")
            st.metric(
                label="Total Liquidity",
                value=f"${float(liquidity):,.2f}" if liquidity else "N/A"
            )

        with col3:
            buy_vol = rayls_analytics.get("total_buy_volume", {})
            st.metric(
                label="24h Buy Volume",
                value=f"${buy_vol.get('24h', 0):,.2f}" if buy_vol.get('24h') else "$0"
            )

        with col4:
            sell_vol = rayls_analytics.get("total_sell_volume", {})
            st.metric(
                label="24h Sell Volume",
                value=f"${sell_vol.get('24h', 0):,.2f}" if sell_vol.get('24h') else "$0"
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Second row of metrics
        col5, col6, col7, col8 = st.columns(4)

        with col5:
            buyers = rayls_analytics.get("total_buyers", {})
            st.metric(
                label="24h Buyers",
                value=f"{buyers.get('24h', 0):,}" if buyers.get('24h') else "0"
            )

        with col6:
            sellers = rayls_analytics.get("total_sellers", {})
            st.metric(
                label="24h Sellers",
                value=f"{sellers.get('24h', 0):,}" if sellers.get('24h') else "0"
            )

        with col7:
            buys = rayls_analytics.get("total_buys", {})
            st.metric(
                label="24h Buy Transactions",
                value=f"{buys.get('24h', 0):,}" if buys.get('24h') else "0"
            )

        with col8:
            sells = rayls_analytics.get("total_sells", {})
            st.metric(
                label="24h Sell Transactions",
                value=f"{sells.get('24h', 0):,}" if sells.get('24h') else "0"
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Multi-period activity charts for Rayls
        st.markdown('<div class="section-header">Rayls Multi-Period Activity</div>', unsafe_allow_html=True)
        st.markdown("Buy/sell volume, wallet activity, and price momentum broken down across all available time windows.")

        periods = ["5m", "1h", "6h", "24h"]

        buy_vol   = rayls_analytics.get("total_buy_volume", {}) or {}
        sell_vol  = rayls_analytics.get("total_sell_volume", {}) or {}
        buyers    = rayls_analytics.get("total_buyers", {}) or {}
        sellers   = rayls_analytics.get("total_sellers", {}) or {}
        price_chg = rayls_analytics.get("price_percent_change", {}) or {}

        mp_col1, mp_col2 = st.columns(2)

        with mp_col1:
            # Buy vs Sell Volume by period
            import plotly.graph_objects as go
            buy_vals  = [buy_vol.get(p, 0) or 0 for p in periods]
            sell_vals = [sell_vol.get(p, 0) or 0 for p in periods]

            fig_vol_mp = go.Figure()
            fig_vol_mp.add_trace(go.Bar(
                x=periods, y=buy_vals,
                name="Buy Volume",
                marker_color="#22c55e",
                text=[f"${v:,.2f}" for v in buy_vals],
                textposition="outside",
            ))
            fig_vol_mp.add_trace(go.Bar(
                x=periods, y=sell_vals,
                name="Sell Volume",
                marker_color="#ef4444",
                text=[f"${v:,.2f}" for v in sell_vals],
                textposition="outside",
            ))
            fig_vol_mp.update_layout(
                title=dict(text="Buy vs Sell Volume by Period", font=dict(size=15)),
                barmode="group",
                height=350,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(tickprefix="$", showgrid=True, gridcolor="rgba(128,128,128,0.2)"),
                xaxis_title="Period",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_vol_mp, width="stretch")

        with mp_col2:
            # Buyers vs Sellers by period
            buyer_vals  = [buyers.get(p, 0) or 0 for p in periods]
            seller_vals = [sellers.get(p, 0) or 0 for p in periods]

            fig_bs_mp = go.Figure()
            fig_bs_mp.add_trace(go.Bar(
                x=periods, y=buyer_vals,
                name="Buyers",
                marker_color="#22c55e",
                text=[str(v) for v in buyer_vals],
                textposition="outside",
            ))
            fig_bs_mp.add_trace(go.Bar(
                x=periods, y=seller_vals,
                name="Sellers",
                marker_color="#ef4444",
                text=[str(v) for v in seller_vals],
                textposition="outside",
            ))
            fig_bs_mp.update_layout(
                title=dict(text="Buyers vs Sellers by Period", font=dict(size=15)),
                barmode="group",
                height=350,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.2)"),
                xaxis_title="Period",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_bs_mp, width="stretch")

        # Price % change across periods — full width
        price_vals = [price_chg.get(p, 0) or 0 for p in periods]
        bar_colors = ["#22c55e" if v >= 0 else "#ef4444" for v in price_vals]

        fig_price_mp = go.Figure(go.Bar(
            x=periods,
            y=price_vals,
            marker_color=bar_colors,
            text=[f"{v:+.2f}%" for v in price_vals],
            textposition="outside",
        ))
        fig_price_mp.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
        fig_price_mp.update_layout(
            title=dict(text="Price % Change by Period", font=dict(size=15)),
            height=300,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Period",
            yaxis=dict(ticksuffix="%", showgrid=True, gridcolor="rgba(128,128,128,0.2)"),
            showlegend=False,
        )
        st.plotly_chart(fig_price_mp, width="stretch")

        st.markdown("<br>", unsafe_allow_html=True)

        # All tokens analytics comparison
        st.markdown('<div class="section-header">Token Analytics Comparison</div>', unsafe_allow_html=True)

        # Build comparison dataframe
        analytics_comparison = []
        for token_name, data in analytics_data.items():
            buy_vol = data.get("total_buy_volume", {})
            sell_vol = data.get("total_sell_volume", {})
            buyers = data.get("total_buyers", {})
            sellers = data.get("total_sellers", {})
            wallets = data.get("unique_wallets", {})
            price_change = data.get("price_percent_change", {})

            # Calculate total buy volume (sum of all periods)
            total_buy = sum([
                buy_vol.get("5m", 0) or 0,
                buy_vol.get("1h", 0) or 0,
                buy_vol.get("6h", 0) or 0,
                buy_vol.get("24h", 0) or 0
            ]) if buy_vol else 0

            analytics_comparison.append({
                "Token": token_name,
                "Chain": data.get("chain", "eth").upper(),
                "USD Price": float(data.get("usd_price", 0)) if data.get("usd_price") else None,
                "Liquidity": float(data.get("total_liquidity_usd", 0)) if data.get("total_liquidity_usd") else None,
                "Total Buy Vol": total_buy,
                "24h Buy Vol": buy_vol.get("24h", 0) if buy_vol else 0,
                "24h Sell Vol": sell_vol.get("24h", 0) if sell_vol else 0,
                "24h Buyers": buyers.get("24h", 0) if buyers else 0,
                "24h Sellers": sellers.get("24h", 0) if sellers else 0,
                "24h Wallets": wallets.get("24h", 0) if wallets else 0,
                "24h Price %": price_change.get("24h", 0) if price_change else 0,
                "Contract": data.get("contract_address", ""),
            })

        analytics_df = pd.DataFrame(analytics_comparison)

        # Sort by liquidity descending
        analytics_df = analytics_df.sort_values("Liquidity", ascending=False, na_position="last")

        # Create bar chart for volume comparison
        chart_data = analytics_df[analytics_df["Liquidity"].notna()].copy()

        if len(chart_data) > 0:
            # Volume comparison chart
            fig_volume = px.bar(
                chart_data,
                x="Token",
                y=["24h Buy Vol", "24h Sell Vol"],
                barmode="group",
                color_discrete_map={"24h Buy Vol": "#22c55e", "24h Sell Vol": "#ef4444"},
                title="24h Trading Volume by Token",
            )

            fig_volume.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis=dict(tickfont=dict(size=12)),
                yaxis=dict(tickfont=dict(size=12), tickprefix="$"),
            )

            st.plotly_chart(fig_volume, width="stretch")

        st.markdown("<br>", unsafe_allow_html=True)

        # Normalized Volume Comparison
        st.markdown('<div class="section-header">Normalized Volume Comparison (Rayls vs Peers)</div>', unsafe_allow_html=True)
        st.markdown("""
        Volume metrics normalized to 0-100 scale for fair comparison across tokens with different trading volumes.
        """)

        if len(chart_data) > 0:
            # Normalize Total Buy Volume (min-max to 0-100)
            max_total_buy = chart_data["Total Buy Vol"].max()
            if max_total_buy > 0:
                chart_data["Normalized Total Buy Vol"] = (chart_data["Total Buy Vol"] / max_total_buy) * 100
            else:
                chart_data["Normalized Total Buy Vol"] = 0

            # Normalize 24h Buy Volume (min-max to 0-100)
            max_24h_buy = chart_data["24h Buy Vol"].max()
            if max_24h_buy > 0:
                chart_data["Normalized 24h Buy Vol"] = (chart_data["24h Buy Vol"] / max_24h_buy) * 100
            else:
                chart_data["Normalized 24h Buy Vol"] = 0

            # Color Rayls differently
            chart_data["Token Type"] = chart_data["Token"].apply(
                lambda x: "Rayls (RLS)" if x == "Rayls (RLS)" else "Peers"
            )

            col_norm1, col_norm2 = st.columns(2)

            with col_norm1:
                # Normalized Total Buy Volume chart
                fig_norm_total = px.bar(
                    chart_data.sort_values("Normalized Total Buy Vol", ascending=True),
                    x="Normalized Total Buy Vol",
                    y="Token",
                    orientation="h",
                    color="Token Type",
                    color_discrete_map={"Rayls (RLS)": "#4299e1", "Peers": "#64748b"},
                    title="Total Buy Volume (Normalized)",
                    text=chart_data.sort_values("Normalized Total Buy Vol", ascending=True)["Normalized Total Buy Vol"].apply(lambda x: f"{x:.1f}")
                )

                fig_norm_total.update_traces(textposition="outside")
                fig_norm_total.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e2e8f0"),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(tickfont=dict(size=11), range=[0, 110], title="Score (0-100)"),
                    yaxis=dict(tickfont=dict(size=11), title=""),
                    height=350,
                )

                st.plotly_chart(fig_norm_total, width="stretch")

            with col_norm2:
                # Normalized 24h Buy Volume chart
                fig_norm_24h = px.bar(
                    chart_data.sort_values("Normalized 24h Buy Vol", ascending=True),
                    x="Normalized 24h Buy Vol",
                    y="Token",
                    orientation="h",
                    color="Token Type",
                    color_discrete_map={"Rayls (RLS)": "#4299e1", "Peers": "#64748b"},
                    title="24h Buy Volume (Normalized)",
                    text=chart_data.sort_values("Normalized 24h Buy Vol", ascending=True)["Normalized 24h Buy Vol"].apply(lambda x: f"{x:.1f}")
                )

                fig_norm_24h.update_traces(textposition="outside")
                fig_norm_24h.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e2e8f0"),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(tickfont=dict(size=11), range=[0, 110], title="Score (0-100)"),
                    yaxis=dict(tickfont=dict(size=11), title=""),
                    height=350,
                )

                st.plotly_chart(fig_norm_24h, width="stretch")

        st.markdown("<br>", unsafe_allow_html=True)

        # Analytics data table
        st.markdown('<div class="section-header">Analytics Data Summary</div>', unsafe_allow_html=True)

        display_analytics_df = analytics_df.copy()
        display_analytics_df["USD Price"] = analytics_df["USD Price"].apply(
            lambda x: f"${x:.6f}" if x and not pd.isna(x) else "N/A"
        )
        display_analytics_df["Liquidity"] = analytics_df["Liquidity"].apply(
            lambda x: f"${x:,.2f}" if x and not pd.isna(x) else "N/A"
        )
        display_analytics_df["Total Buy Vol"] = analytics_df["Total Buy Vol"].apply(
            lambda x: f"${x:,.2f}" if x else "$0"
        )
        display_analytics_df["24h Buy Vol"] = analytics_df["24h Buy Vol"].apply(
            lambda x: f"${x:,.2f}" if x else "$0"
        )
        display_analytics_df["24h Sell Vol"] = analytics_df["24h Sell Vol"].apply(
            lambda x: f"${x:,.2f}" if x else "$0"
        )
        display_analytics_df["24h Price %"] = analytics_df["24h Price %"].apply(
            lambda x: f"{x:+.2f}%" if x else "0%"
        )
        display_analytics_df["Contract"] = analytics_df["Contract"].apply(
            lambda x: x[:10] + "..." + x[-6:] if x else "N/A"
        )

        st.dataframe(
            display_analytics_df[["Token", "Chain", "USD Price", "Liquidity", "Total Buy Vol", "24h Buy Vol", "24h Sell Vol", "24h Buyers", "24h Sellers", "24h Wallets", "24h Price %"]],
            width="stretch",
            hide_index=True,
            column_config={
                "Token": st.column_config.TextColumn("Token", width="medium"),
                "Chain": st.column_config.TextColumn("Chain", width="small"),
                "USD Price": st.column_config.TextColumn("USD Price", width="small"),
                "Liquidity": st.column_config.TextColumn("Liquidity", width="medium"),
                "Total Buy Vol": st.column_config.TextColumn("Total Buy Vol", width="small"),
                "24h Buy Vol": st.column_config.TextColumn("24h Buy Vol", width="small"),
                "24h Sell Vol": st.column_config.TextColumn("24h Sell Vol", width="small"),
                "24h Buyers": st.column_config.NumberColumn("Buyers", width="small"),
                "24h Sellers": st.column_config.NumberColumn("Sellers", width="small"),
                "24h Wallets": st.column_config.NumberColumn("Wallets", width="small"),
                "24h Price %": st.column_config.TextColumn("24h Price %", width="small"),
            }
        )

    else:
        st.warning("Unable to load token analytics data. Please check your Moralis API key.")

# Tab 6: Market Analytics (Kraken)
with tab6:
    st.markdown('<div class="section-header">Market Analytics (Kraken)</div>', unsafe_allow_html=True)
    st.markdown("""
    Spot market analytics for Rayls and peer tokens from **Kraken** (public data, no API key required, globally accessible).
    Tokens not listed on Kraken are automatically skipped.
    """)

    @st.cache_data(ttl=600)
    def load_peer_comparison():
        """Load comparison data for all tokens on Kraken."""
        return kraken_market.get_peer_comparison()

    @st.cache_data(ttl=600)
    def load_kraken_ohlc(pair, interval, limit=100):
        """Load OHLC data for a specific pair and interval."""
        return kraken_market.get_ohlc(pair=pair, interval=interval, limit=limit)

    @st.cache_data(ttl=600)
    def load_kraken_full(pair):
        """Load full market data for a single token."""
        return kraken_market.get_all_market_data(pair)

    with st.spinner("Loading market data from Kraken for all tokens..."):
        peer_data = load_peer_comparison()

    available_tokens = list(peer_data.keys())

    if not available_tokens:
        st.warning("Unable to load data from Kraken for any token.")
    else:
        # ============================================================
        # SECTION 1: Peer Comparison Overview
        # ============================================================
        st.markdown("#### Peer Comparison Overview")
        st.caption(f"Showing {len(available_tokens)} tokens available on Kraken. Ondo Yield Assets (USDY) is not listed on Kraken and is excluded.")

        # Build comparison table
        comp_rows = []
        for name in available_tokens:
            t = peer_data[name]["ticker"]
            book = peer_data[name].get("order_book")
            trades = peer_data[name].get("trades")

            mid = (t["ask"] + t["bid"]) / 2 if (t["ask"] + t["bid"]) else 0
            spread_bps = (t["spread"] / mid * 10000) if mid else 0

            row = {
                "Token": name,
                "Price (USD)": t["last_price"],
                "24h Change (%)": t["price_change_pct"],
                "24h Volume": t["volume"],
                "VWAP": t["vwap"],
                "24h High": t["high"],
                "24h Low": t["low"],
                "Trades (24h)": t["trade_count"],
                "Spread (bps)": round(spread_bps, 1),
            }

            if book:
                row["Bid/Ask Ratio"] = book["bid_ask_ratio"]
                row["Bid Vol %"] = book["bid_pct"]
            else:
                row["Bid/Ask Ratio"] = None
                row["Bid Vol %"] = None

            if trades:
                row["Buy/Sell Ratio"] = trades["buy_sell_ratio"]
                row["Buy Vol %"] = trades["buy_pct"]
            else:
                row["Buy/Sell Ratio"] = None
                row["Buy Vol %"] = None

            comp_rows.append(row)

        comp_df = pd.DataFrame(comp_rows)

        st.dataframe(
            comp_df,
            width="stretch",
            hide_index=True,
            column_config={
                "Price (USD)": st.column_config.NumberColumn(format="$%.6f"),
                "24h Change (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "24h Volume": st.column_config.NumberColumn(format="%.0f"),
                "VWAP": st.column_config.NumberColumn(format="$%.6f"),
                "24h High": st.column_config.NumberColumn(format="$%.6f"),
                "24h Low": st.column_config.NumberColumn(format="$%.6f"),
                "Trades (24h)": st.column_config.NumberColumn(format="%d"),
                "Spread (bps)": st.column_config.NumberColumn(format="%.1f"),
                "Bid/Ask Ratio": st.column_config.NumberColumn(format="%.4f"),
                "Bid Vol %": st.column_config.NumberColumn(format="%.1f%%"),
                "Buy/Sell Ratio": st.column_config.NumberColumn(format="%.4f"),
                "Buy Vol %": st.column_config.NumberColumn(format="%.1f%%"),
            },
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Comparison Charts (2x2) ---
        import plotly.graph_objects as go

        comp_chart_col1, comp_chart_col2 = st.columns(2)

        # 24h Price Change comparison
        with comp_chart_col1:
            st.markdown("##### 24h Price Change (%)")
            names = [r["Token"] for r in comp_rows]
            changes = [r["24h Change (%)"] for r in comp_rows]
            bar_colors = ["#68d391" if c >= 0 else "#fc8181" for c in changes]

            fig_change = go.Figure(go.Bar(
                x=names, y=changes,
                marker_color=bar_colors,
                text=[f"{c:+.2f}%" for c in changes],
                textposition="outside",
            ))
            fig_change.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
            fig_change.update_layout(
                height=350,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title="", yaxis_title="Change (%)",
                showlegend=False,
            )
            fig_change.update_xaxes(showgrid=False)
            fig_change.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
            st.plotly_chart(fig_change, width="stretch")

        # Buy/Sell Ratio comparison
        with comp_chart_col2:
            st.markdown("##### Buy/Sell Volume Ratio (Recent Trades)")
            bs_names = [r["Token"] for r in comp_rows if r.get("Buy/Sell Ratio") is not None]
            bs_ratios = [r["Buy/Sell Ratio"] for r in comp_rows if r.get("Buy/Sell Ratio") is not None]
            bs_colors = ["#68d391" if r >= 1.0 else "#fc8181" for r in bs_ratios]

            if bs_names:
                fig_bs_comp = go.Figure(go.Bar(
                    x=bs_names, y=bs_ratios,
                    marker_color=bs_colors,
                    text=[f"{r:.2f}" for r in bs_ratios],
                    textposition="outside",
                ))
                fig_bs_comp.add_hline(y=1.0, line_dash="dash", line_color="#ecc94b", opacity=0.6,
                                      annotation_text="Neutral (1.0)", annotation_position="top right")
                fig_bs_comp.update_layout(
                    height=350,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="", yaxis_title="Buy/Sell Ratio",
                    showlegend=False,
                )
                fig_bs_comp.update_xaxes(showgrid=False)
                fig_bs_comp.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
                st.plotly_chart(fig_bs_comp, width="stretch")
            else:
                st.info("No trade data available for comparison.")

        comp_chart_col3, comp_chart_col4 = st.columns(2)

        # Order Book Imbalance comparison
        with comp_chart_col3:
            st.markdown("##### Order Book Imbalance (Bid/Ask Ratio)")
            ob_names = [r["Token"] for r in comp_rows if r.get("Bid/Ask Ratio") is not None]
            ob_ratios = [r["Bid/Ask Ratio"] for r in comp_rows if r.get("Bid/Ask Ratio") is not None]
            ob_colors = ["#68d391" if r >= 1.0 else "#fc8181" for r in ob_ratios]

            if ob_names:
                fig_ob_comp = go.Figure(go.Bar(
                    x=ob_names, y=ob_ratios,
                    marker_color=ob_colors,
                    text=[f"{r:.2f}" for r in ob_ratios],
                    textposition="outside",
                ))
                fig_ob_comp.add_hline(y=1.0, line_dash="dash", line_color="#ecc94b", opacity=0.6,
                                      annotation_text="Balanced (1.0)", annotation_position="top right")
                fig_ob_comp.update_layout(
                    height=350,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="", yaxis_title="Bid/Ask Ratio",
                    showlegend=False,
                )
                fig_ob_comp.update_xaxes(showgrid=False)
                fig_ob_comp.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
                st.plotly_chart(fig_ob_comp, width="stretch")
            else:
                st.info("No order book data available for comparison.")

        # Spread comparison
        with comp_chart_col4:
            st.markdown("##### Bid-Ask Spread (bps)")
            sp_names = [r["Token"] for r in comp_rows]
            sp_bps = [r["Spread (bps)"] for r in comp_rows]
            # Lower spread = better liquidity (green), higher = worse (red)
            sp_colors = ["#68d391" if s <= 30 else ("#ecc94b" if s <= 60 else "#fc8181") for s in sp_bps]

            fig_sp_comp = go.Figure(go.Bar(
                x=sp_names, y=sp_bps,
                marker_color=sp_colors,
                text=[f"{s:.1f}" for s in sp_bps],
                textposition="outside",
            ))
            fig_sp_comp.update_layout(
                height=350,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title="", yaxis_title="Spread (bps)",
                showlegend=False,
            )
            fig_sp_comp.update_xaxes(showgrid=False)
            fig_sp_comp.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
            st.plotly_chart(fig_sp_comp, width="stretch")

        st.markdown("<br>", unsafe_allow_html=True)

        # ============================================================
        # SECTION 2: Detailed Single-Token Analysis
        # ============================================================
        st.markdown("---")
        st.markdown("#### Detailed Token Analysis")

        selected_token = st.selectbox(
            "Select Token",
            available_tokens,
            index=available_tokens.index("Rayls") if "Rayls" in available_tokens else 0,
            key="kraken_detail_token",
        )

        selected_pair = kraken_market.KRAKEN_PAIRS.get(selected_token, "RLSUSD")

        with st.spinner(f"Loading detailed data for {selected_token}..."):
            detail_data = load_kraken_full(selected_pair)

        ticker = detail_data.get("ticker", {})
        order_book = detail_data.get("order_book", {})
        trades_data = detail_data.get("trades", {})
        spread_data = detail_data.get("spread", {})

        # --- KPI Rows ---
        if not (isinstance(ticker, dict) and "error" in ticker):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="Spot Price", value=f"${ticker.get('last_price', 0):.6f}")
            with col2:
                pct = ticker.get("price_change_pct", 0)
                st.metric(label="24h Change", value=f"{pct:+.2f}%")
            with col3:
                vol = ticker.get("volume", 0)
                if vol >= 1_000_000:
                    vol_str = f"{vol / 1_000_000:.2f}M"
                elif vol >= 1_000:
                    vol_str = f"{vol / 1_000:.2f}K"
                else:
                    vol_str = f"{vol:,.2f}"
                st.metric(label="24h Volume", value=vol_str)
            with col4:
                st.metric(label="24h Trades", value=f"{ticker.get('trade_count', 0):,}")

            col5, col6, col7, col8 = st.columns(4)
            with col5:
                st.metric(label="VWAP", value=f"${ticker.get('vwap', 0):.6f}")
            with col6:
                st.metric(label="24h High", value=f"${ticker.get('high', 0):.6f}")
            with col7:
                st.metric(label="24h Low", value=f"${ticker.get('low', 0):.6f}")
            with col8:
                spread_val = ticker.get("spread", 0)
                bid = ticker.get("bid", 0)
                ask = ticker.get("ask", 0)
                mid = (bid + ask) / 2 if (bid + ask) else 0
                spread_bps_val = (spread_val / mid * 10000) if mid else 0
                st.metric(label="Bid-Ask Spread", value=f"${spread_val:.6f}", help=f"{spread_bps_val:.1f} bps")
        else:
            st.warning(f"Unable to load ticker data: {ticker.get('error', 'Unknown error')}")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Candlestick Chart ---
        st.markdown(f"#### {selected_token} Price Chart (Candlestick + Volume)")
        candle_interval = st.selectbox("Interval", ["1d", "4h", "1h"], index=0, key="kraken_candle_interval")
        candle_limit = {"1d": 60, "4h": 120, "1h": 168}.get(candle_interval, 60)
        klines_df = load_kraken_ohlc(selected_pair, candle_interval, limit=candle_limit)

        if isinstance(klines_df, pd.DataFrame) and not klines_df.empty:
            from plotly.subplots import make_subplots

            fig_candle = make_subplots(
                rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
            )
            fig_candle.add_trace(
                go.Candlestick(
                    x=klines_df["timestamp"],
                    open=klines_df["open"],
                    high=klines_df["high"],
                    low=klines_df["low"],
                    close=klines_df["close"],
                    increasing_line_color="#68d391",
                    decreasing_line_color="#fc8181",
                    name="Price",
                ),
                row=1, col=1,
            )
            colors = ["#68d391" if c >= o else "#fc8181" for c, o in zip(klines_df["close"], klines_df["open"])]
            fig_candle.add_trace(
                go.Bar(
                    x=klines_df["timestamp"],
                    y=klines_df["volume"],
                    marker_color=colors,
                    name="Volume",
                    opacity=0.6,
                ),
                row=2, col=1,
            )
            fig_candle.update_layout(
                height=550,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_rangeslider_visible=False,
                showlegend=False,
            )
            fig_candle.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
            fig_candle.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
            st.plotly_chart(fig_candle, width="stretch")
        elif isinstance(klines_df, dict) and "error" in klines_df:
            st.warning(f"Unable to load OHLC data: {klines_df['error']}")
        else:
            st.info("No OHLC data available.")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Market Indicators (2x2 grid) ---
        st.markdown(f"#### {selected_token} Market Indicators")
        ind_col1, ind_col2 = st.columns(2)

        # Order Book Depth
        with ind_col1:
            st.markdown("##### Order Book Depth")
            if isinstance(order_book, dict) and "error" not in order_book:
                asks = order_book["asks"]
                bids = order_book["bids"]

                bid_prices = [b["price"] for b in sorted(bids, key=lambda x: x["price"], reverse=True)]
                bid_cum = []
                cumsum = 0
                for b in sorted(bids, key=lambda x: x["price"], reverse=True):
                    cumsum += b["volume"]
                    bid_cum.append(cumsum)

                ask_prices = [a["price"] for a in sorted(asks, key=lambda x: x["price"])]
                ask_cum = []
                cumsum = 0
                for a in sorted(asks, key=lambda x: x["price"]):
                    cumsum += a["volume"]
                    ask_cum.append(cumsum)

                fig_depth = go.Figure()
                fig_depth.add_trace(go.Scatter(
                    x=bid_prices, y=bid_cum,
                    fill="tozeroy", name="Bids",
                    line=dict(color="#68d391"), fillcolor="rgba(104,211,145,0.3)",
                ))
                fig_depth.add_trace(go.Scatter(
                    x=ask_prices, y=ask_cum,
                    fill="tozeroy", name="Asks",
                    line=dict(color="#fc8181"), fillcolor="rgba(252,129,129,0.3)",
                ))
                fig_depth.update_layout(
                    height=350,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="Price (USD)",
                    yaxis_title="Cumulative Volume",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                fig_depth.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
                fig_depth.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
                st.plotly_chart(fig_depth, width="stretch")

                bid_pct = order_book.get("bid_pct", 50)
                ask_pct = order_book.get("ask_pct", 50)
                ratio = order_book.get("bid_ask_ratio", 1.0)
                signal = "Bullish" if ratio > 1.2 else ("Bearish" if ratio < 0.8 else "Neutral")
                st.caption(f"Bid Volume: {bid_pct:.0f}% | Ask Volume: {ask_pct:.0f}% | Ratio: {ratio:.4f} — **{signal}**")
            else:
                error_msg = order_book.get("error", "Unknown error") if isinstance(order_book, dict) else "Unknown error"
                st.info(f"Order book data unavailable: {error_msg}")

        # Trade Buy/Sell Breakdown
        with ind_col2:
            st.markdown("##### Buy vs Sell Volume (Recent Trades)")
            if isinstance(trades_data, dict) and "error" not in trades_data:
                buy_vol = trades_data.get("buy_volume", 0)
                sell_vol = trades_data.get("sell_volume", 0)
                buy_count = trades_data.get("buy_count", 0)
                sell_count = trades_data.get("sell_count", 0)

                fig_bs = go.Figure()
                fig_bs.add_trace(go.Bar(
                    x=["Volume"], y=[buy_vol],
                    name="Buy Volume", marker_color="#68d391",
                ))
                fig_bs.add_trace(go.Bar(
                    x=["Volume"], y=[sell_vol],
                    name="Sell Volume", marker_color="#fc8181",
                ))
                fig_bs.add_trace(go.Bar(
                    x=["Trade Count"], y=[buy_count],
                    name="Buy Trades", marker_color="#68d391", showlegend=False,
                ))
                fig_bs.add_trace(go.Bar(
                    x=["Trade Count"], y=[sell_count],
                    name="Sell Trades", marker_color="#fc8181", showlegend=False,
                ))
                fig_bs.update_layout(
                    height=350,
                    barmode="group",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    yaxis_title="",
                )
                fig_bs.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
                st.plotly_chart(fig_bs, width="stretch")

                ratio = trades_data.get("buy_sell_ratio", 1.0)
                buy_pct = trades_data.get("buy_pct", 50)
                signal = "Bullish" if ratio > 1.1 else ("Bearish" if ratio < 0.9 else "Neutral")
                st.caption(f"Buy/Sell Ratio: {ratio:.4f} ({buy_pct:.0f}% buys) — **{signal}**")
            else:
                error_msg = trades_data.get("error", "Unknown error") if isinstance(trades_data, dict) else "Unknown error"
                st.info(f"Trade data unavailable: {error_msg}")

        ind_col3, ind_col4 = st.columns(2)

        # Spread History
        with ind_col3:
            st.markdown("##### Bid-Ask Spread History")
            if isinstance(spread_data, dict) and "error" not in spread_data:
                spread_df = spread_data.get("df", pd.DataFrame())
                if not spread_df.empty:
                    fig_spread = px.area(
                        spread_df,
                        x="timestamp",
                        y="spread_bps",
                        color_discrete_sequence=["#4299e1"],
                    )
                    fig_spread.update_layout(
                        height=350,
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        xaxis_title="",
                        yaxis_title="Spread (basis points)",
                    )
                    fig_spread.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
                    fig_spread.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
                    st.plotly_chart(fig_spread, width="stretch")
                    st.caption(f"Current: {spread_data.get('current_spread_bps', 0):.1f} bps | Avg: {spread_data.get('avg_spread_bps', 0):.1f} bps")
                else:
                    st.info("No spread history data available.")
            else:
                error_msg = spread_data.get("error", "Unknown error") if isinstance(spread_data, dict) else "Unknown error"
                st.info(f"Spread data unavailable: {error_msg}")

        # Trade Timeline
        with ind_col4:
            st.markdown("##### Recent Trade Activity")
            if isinstance(trades_data, dict) and "error" not in trades_data:
                trade_df = trades_data.get("df", pd.DataFrame())
                if not trade_df.empty:
                    trade_df_copy = trade_df.copy()
                    trade_df_copy = trade_df_copy.set_index("timestamp")
                    hourly = trade_df_copy.groupby([pd.Grouper(freq="1h"), "side"])["volume"].sum().unstack(fill_value=0).reset_index()

                    if "buy" in hourly.columns or "sell" in hourly.columns:
                        fig_timeline = go.Figure()
                        if "buy" in hourly.columns:
                            fig_timeline.add_trace(go.Bar(
                                x=hourly["timestamp"], y=hourly["buy"],
                                name="Buy Volume", marker_color="#68d391",
                            ))
                        if "sell" in hourly.columns:
                            fig_timeline.add_trace(go.Bar(
                                x=hourly["timestamp"], y=hourly["sell"],
                                name="Sell Volume", marker_color="#fc8181",
                            ))
                        fig_timeline.update_layout(
                            height=350,
                            barmode="stack",
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            xaxis_title="",
                            yaxis_title="Volume",
                        )
                        fig_timeline.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
                        fig_timeline.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
                        st.plotly_chart(fig_timeline, width="stretch")
                    else:
                        st.info("Not enough trade data for timeline.")
                else:
                    st.info("No trade data available.")
            else:
                error_msg = trades_data.get("error", "Unknown error") if isinstance(trades_data, dict) else "Unknown error"
                st.info(f"Trade timeline unavailable: {error_msg}")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Market Signal Summary ---
        st.markdown(f"#### {selected_token} Market Signal Summary")
        signal_result = kraken_market.compute_market_signal(detail_data)
        overall = signal_result["overall_signal"]
        score = signal_result["signal_score"]
        factors = signal_result["factors"]

        signal_colors = {"Bullish": "#68d391", "Bearish": "#fc8181", "Neutral": "#ecc94b"}
        signal_color = signal_colors.get(overall, "#ecc94b")

        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid {signal_color}; padding: 1.5rem;">
            <div class="metric-label">OVERALL SIGNAL — {selected_token.upper()}</div>
            <div class="metric-value" style="color: {signal_color};">{overall}</div>
            <div style="color: #cbd5e1; font-size: 1rem;">Score: {score:+.3f} (range: -1.0 bearish to +1.0 bullish)</div>
        </div>
        """, unsafe_allow_html=True)

        if factors:
            factors_df = pd.DataFrame(factors)
            factors_df.columns = ["Factor", "Value", "Signal", "Weight", "Score"]
            st.dataframe(factors_df, width="stretch", hide_index=True)

            if overall == "Bullish":
                st.markdown("""
                > **Interpretation:** The weighted market indicators lean bullish. Buying pressure exceeds selling pressure
                > and order book support is strong. Monitor spread and volume for confirmation.
                """)
            elif overall == "Bearish":
                st.markdown("""
                > **Interpretation:** The weighted market indicators lean bearish. Selling pressure exceeds buying pressure
                > and/or liquidity is thinning. Watch for support levels and volume changes.
                """)
            else:
                st.markdown("""
                > **Interpretation:** Market indicators are mixed with no strong directional bias.
                > Market is in a consolidation phase. Watch for a breakout in either direction.
                """)

# Tab 7: Whale Tracker
with tab7:
    st.markdown('<div class="section-header">Whale Tracker</div>', unsafe_allow_html=True)
    st.markdown("""
    Monitor whale behavior, accumulation patterns, and exchange flows for Rayls (RLS). Data powered by **Etherscan API**.
    """)

    rayls_contract = "0xB5F7b021a78f470d31D762C1DDA05ea549904fbd"
    rayls_chain = "eth"

    @st.cache_data(ttl=600)
    def load_whale_data():
        """Load whale tracker data for Rayls."""
        whale_transfers = etherscan.get_whale_transfers(rayls_contract, rayls_chain, min_tokens=100000, limit=50)
        accumulation = etherscan.get_whale_accumulation_indicator(rayls_contract, rayls_chain, days=7)
        exchange_flow = etherscan.get_exchange_flow_analysis(rayls_contract, rayls_chain, days=7)
        return whale_transfers, accumulation, exchange_flow

    with st.spinner("Loading whale tracker data from Etherscan..."):
        whale_transfers_data, accumulation_data, exchange_flow_data = load_whale_data()

    # Section 1: Accumulation Score
    if isinstance(accumulation_data, dict) and "error" not in accumulation_data:
        st.markdown('<div class="section-header">Whale Accumulation Indicator (7 Days)</div>', unsafe_allow_html=True)

        score = accumulation_data.get("score", 0)
        acc_count = accumulation_data.get("accumulating_count", 0)
        dist_count = accumulation_data.get("distributing_count", 0)
        neutral_count = accumulation_data.get("neutral_count", 0)

        # Determine signal
        if score > 0.2:
            signal_text = "Bullish"
            signal_color = "#68d391"
        elif score < -0.2:
            signal_text = "Bearish"
            signal_color = "#feb2b2"
        else:
            signal_text = "Neutral"
            signal_color = "#e2e8f0"

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Accumulation Score",
                value=f"{score:+.2f}",
                help="Ranges from -1.0 (all distributing) to +1.0 (all accumulating)"
            )

        with col2:
            st.metric(
                label="Accumulating Wallets",
                value=f"{acc_count}",
            )

        with col3:
            st.metric(
                label="Distributing Wallets",
                value=f"{dist_count}",
            )

        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">SIGNAL</div>
                <div class="metric-value" style="color: {signal_color};">{signal_text}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Top 20 Addresses Net Flow - horizontal bar
        st.markdown("#### Top 20 Addresses by Volume - Net Flow")

        top_addresses = accumulation_data.get("top_addresses", [])
        if top_addresses:
            addr_df = pd.DataFrame(top_addresses)
            addr_df["short_address"] = addr_df["address"].apply(lambda x: f"{x[:6]}...{x[-4:]}")
            addr_df["bar_color"] = addr_df["status"].map({
                "Accumulating": "#22c55e",
                "Distributing": "#ef4444",
                "Neutral": "#94a3b8",
            })

            import plotly.graph_objects as go

            fig_whale_flow = go.Figure()

            for _, row in addr_df.iterrows():
                fig_whale_flow.add_trace(go.Bar(
                    x=[row["net_flow"]],
                    y=[row["short_address"]],
                    orientation="h",
                    marker=dict(color=row["bar_color"]),
                    name=row["status"],
                    showlegend=False,
                    hovertemplate=f"<b>{row['address']}</b><br>Net Flow: {row['net_flow']:,.2f}<br>Status: {row['status']}<extra></extra>",
                ))

            fig_whale_flow.update_layout(
                height=500,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Net Token Flow (positive = accumulating)",
                yaxis_title="",
                margin=dict(l=120),
            )
            fig_whale_flow.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")

            # Add legend manually
            fig_whale_flow.add_trace(go.Bar(x=[None], y=[None], marker=dict(color="#22c55e"), name="Accumulating", showlegend=True))
            fig_whale_flow.add_trace(go.Bar(x=[None], y=[None], marker=dict(color="#ef4444"), name="Distributing", showlegend=True))
            fig_whale_flow.add_trace(go.Bar(x=[None], y=[None], marker=dict(color="#94a3b8"), name="Neutral", showlegend=True))

            fig_whale_flow.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )

            st.plotly_chart(fig_whale_flow, width="stretch")
        else:
            st.info("No address flow data available.")
    else:
        error_msg = accumulation_data.get("error", "Unknown error") if isinstance(accumulation_data, dict) else "Unknown error"
        st.warning(f"Unable to load accumulation data: {error_msg}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Section 2: Recent Large Transfers
    st.markdown('<div class="section-header">Recent Large Transfers (>100K tokens)</div>', unsafe_allow_html=True)

    if isinstance(whale_transfers_data, list) and whale_transfers_data:
        whale_df = pd.DataFrame(whale_transfers_data)
        st.dataframe(
            whale_df,
            width="stretch",
            hide_index=True,
            column_config={
                "hash": st.column_config.TextColumn("Tx Hash", width="medium"),
                "from": st.column_config.TextColumn("From", width="medium"),
                "to": st.column_config.TextColumn("To", width="medium"),
                "value": st.column_config.NumberColumn("Value (tokens)", format="%.2f"),
                "timestamp": st.column_config.TextColumn("Timestamp", width="small"),
            },
        )
    elif isinstance(whale_transfers_data, dict) and "error" in whale_transfers_data:
        st.warning(f"Unable to load whale transfers: {whale_transfers_data['error']}")
    else:
        st.info("No large whale transfers found in the last 30 days.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Section 3: Exchange Flow Analysis
    st.markdown('<div class="section-header">Exchange Flow Analysis (7 Days)</div>', unsafe_allow_html=True)

    if isinstance(exchange_flow_data, dict) and "error" not in exchange_flow_data:
        total_inflow = exchange_flow_data.get("total_inflow", 0)
        total_outflow = exchange_flow_data.get("total_outflow", 0)
        net_flow = exchange_flow_data.get("net_flow", 0)
        flow_signal = exchange_flow_data.get("signal", "Neutral")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Exchange Inflow",
                value=format_currency(total_inflow) if total_inflow else "0",
                help="Tokens sent TO exchanges (selling pressure)"
            )

        with col2:
            st.metric(
                label="Exchange Outflow",
                value=format_currency(total_outflow) if total_outflow else "0",
                help="Tokens sent FROM exchanges (buying/accumulation)"
            )

        with col3:
            st.metric(
                label="Net Flow",
                value=format_currency(abs(net_flow)) if net_flow else "0",
                delta=f"{'Outflow' if net_flow > 0 else 'Inflow'}" if net_flow != 0 else None,
                delta_color="normal" if net_flow > 0 else "inverse"
            )

        with col4:
            if flow_signal == "Bullish":
                signal_color = "#68d391"
                signal_desc = "Net outflow from exchanges (accumulation)"
            elif flow_signal == "Bearish":
                signal_color = "#feb2b2"
                signal_desc = "Net inflow to exchanges (selling pressure)"
            else:
                signal_color = "#e2e8f0"
                signal_desc = "Balanced exchange flows"

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">EXCHANGE SIGNAL</div>
                <div class="metric-value" style="color: {signal_color};">{flow_signal}</div>
                <div style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.25rem;">{signal_desc}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Exchange flow bar chart
        exchange_flows = exchange_flow_data.get("exchange_flows", {})
        if exchange_flows:
            st.markdown("#### Inflow vs Outflow by Exchange")

            exchange_chart_data = []
            for exchange_name, flows in exchange_flows.items():
                exchange_chart_data.append({"Exchange": exchange_name, "Flow": flows["inflow"], "Type": "Inflow (Selling)"})
                exchange_chart_data.append({"Exchange": exchange_name, "Flow": flows["outflow"], "Type": "Outflow (Buying)"})

            if exchange_chart_data:
                exchange_df = pd.DataFrame(exchange_chart_data)

                fig_exchange = px.bar(
                    exchange_df,
                    x="Exchange",
                    y="Flow",
                    color="Type",
                    barmode="group",
                    color_discrete_map={"Inflow (Selling)": "#ef4444", "Outflow (Buying)": "#22c55e"},
                )
                fig_exchange.update_layout(
                    height=400,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    yaxis_title="Token Volume",
                    xaxis_title="",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""),
                )
                fig_exchange.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
                st.plotly_chart(fig_exchange, width="stretch")
        else:
            st.info("No exchange flow data detected. This may indicate Rayls tokens are not actively traded on major centralized exchanges tracked.")

        # Interpretation
        st.markdown("---")
        st.markdown("""
        **How to read Exchange Flows:**
        - **Inflow** (tokens sent TO exchanges) = potential **selling pressure** as holders move tokens to exchanges to sell
        - **Outflow** (tokens sent FROM exchanges) = potential **buying/accumulation** as buyers withdraw tokens to hold
        - **Net Outflow** is generally **bullish** — more tokens leaving exchanges than entering
        - **Net Inflow** is generally **bearish** — more tokens entering exchanges, potentially for selling
        """)
    else:
        error_msg = exchange_flow_data.get("error", "Unknown error") if isinstance(exchange_flow_data, dict) else "Unknown error"
        st.warning(f"Unable to load exchange flow data: {error_msg}")

# Footer with refresh button
st.markdown("<br>", unsafe_allow_html=True)
st.divider()

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    elapsed_sec = int((datetime.now() - st.session_state.last_refresh).total_seconds())
    if elapsed_sec < 60:
        freshness_str = f"{elapsed_sec}s ago"
    else:
        freshness_str = f"{elapsed_sec // 60}m {elapsed_sec % 60}s ago"
    st.caption(f"Last updated: {freshness_str}")
    if st.button("🔄 Refresh Data", width="stretch"):
        st.cache_data.clear()
        st.session_state.last_refresh = datetime.now()
        st.rerun()

st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.85rem; margin-top: 1rem;">
    Data refreshes automatically every 5 minutes • Prices from CoinMarketCap • Historical data from CoinGecko • Holder data from Moralis • Market data from Kraken • On-chain data from Etherscan
</div>
""", unsafe_allow_html=True)
