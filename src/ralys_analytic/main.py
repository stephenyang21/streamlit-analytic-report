
import pandas as pd
import matplotlib.pyplot as plt 
from defillama_sdk import DefiLlama
from datetime import datetime 

from metric import tvl
from metric import revenue
from metric import price

client = DefiLlama()
protocols = client.tvl.getProtocols()

allowedProtocol = ["zkSync Era",  "Plume Mainnet","Avalanche","Ondo Finance","Ondo Yield Assets"]                                                                                
# filteredProtocols = [protocol for protocol in protocols if protocol["name"] in allowedProtocol]     


chains = client.tvl.getChains()
allowedChain = ["Polygon"]#"Polygon zkEVM"]
# filteredChain = [chain for chain in chains if chain["name"] in allowedChain]  



#MAX SUPPLY
metadata = [("zksync_era", 21_000_000_000,"era:0x5A7d6b2F92C77FAD6CCaBd7EE0624E64907Eaf3E"),
          ("plume_mainnet",10_000_000_000,"ethereum:0x4C1746A800D224393fE2470C70A35717eD4eA5F1"),
          ("avalanche",715_740_000,"coingecko:avalanche-2" ),
          ("ondo_finance",  10_000_000_000,"ethereum:0xfaba6f8e4a5e8ab82f62fe7c39859fa577269be3"),
          ("ondo_yield_assets",  1_250_000_000, "ethereum:0x96f6ef951840721adbf46ac996b59e0235cb985c"),
          ("polygon",10_000_000_000,"ethereum:0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0"),
]




updated_metadata = []
for token in metadata:
    priceToken = price.getLatestTokenPrice(client,[token[2]])

    calculateFDV = priceToken*token[1]

    updated_metadata.append(token + (calculateFDV,))



# Get 2025 revenue only
def get_2025_revenue(revenue_data):
    annual_data = revenue.annualRevenue(revenue_data)
    for year, total in annual_data:
        if year == "2025":
            return total
    return None


#Process Protocols
print("\n=== Protocol FDV/Revenue Multiplier (2025) ===")
for protocol in allowedProtocol:
    protocol_name = protocol
    try:
        revenue_data = revenue.getRevenueByProtocol(client, protocol_name)
        revenue_2025 = get_2025_revenue(revenue_data)

        # Find matching metadata for FDV
        matching_meta = None
        for meta in updated_metadata:
            # Match by converting names (e.g., "zkSync Era" -> "zksync_era")
            meta_name = meta[0].replace("_", " ").title()
            if meta_name.lower() in protocol_name.lower() or protocol_name.lower().replace(" ", "_") in meta[0]:
                matching_meta = meta
                break

        if matching_meta and revenue_2025 and revenue_2025 > 0:
            fdv = matching_meta[3]  # FDV is the 4th element (index 3)
            multiplier = fdv / revenue_2025
            print(f"{protocol_name}: FDV=${fdv:,.2f}, Revenue 2025=${revenue_2025:,.2f}, Multiplier={multiplier:,.2f}x")
        else:
            print(f"{protocol_name}: No 2025 revenue data or no matching FDV")
    except Exception as e:
        print(f"{protocol_name}: Error - {e}")


# Process Chains
print("\n=== Chain FDV/Revenue Multiplier (2025) ===")
for chain in allowedChain:
    chain_name = chain
    try:
        revenue_data = revenue.getRevenueByChain(client, chain_name)
        revenue_2025 = get_2025_revenue(revenue_data)

        # Find matching metadata for FDV
        matching_meta = None
        for meta in updated_metadata:
            meta_name = meta[0].replace("_", " ").title()
            if meta_name.lower() in chain_name.lower() or chain_name.lower().replace(" ", "_") in meta[0]:
                matching_meta = meta
                break

        if matching_meta and revenue_2025 and revenue_2025 > 0:
            fdv = matching_meta[3]  # FDV is the 4th element (index 3)
            multiplier = fdv / revenue_2025
            print(f"{chain_name}: FDV=${fdv:,.2f}, Revenue 2025=${revenue_2025:,.2f}, Multiplier={multiplier:,.2f}x")
        else:
            print(f"{chain_name}: No 2025 revenue data or no matching FDV")
    except Exception as e:
        print(f"{chain_name}: Error - {e}")


rayls_price = price.getRaylsPrice()
RAYLS_TOKEN_SUPPLY = 10_000_000_000
RAYLS_REVENUE = 2_000_000

RAYLS_FDV =  RAYLS_TOKEN_SUPPLY* rayls_price['price_usd']

MULTIPLIER = RAYLS_FDV/RAYLS_REVENUE
print(f"Rayls FDV {MULTIPLIER:,.2f}")