import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Token contract addresses
TOKEN_CONTRACTS = {
    "Rayls (RLS)": {"address": "0xB5F7b021a78f470d31D762C1DDA05ea549904fbd", "chain": "eth"},
    "Ondo Finance": {"address": "0xfAbA6f8e4a5E8Ab82F62fe7C39859FA577269BE3", "chain": "eth"},
    "Ondo Yield Assets": {"address": "0x96F6eF951840721AdBF46Ac996b59E0235CB985C", "chain": "eth"},
    "Polygon": {"address": "0x455e53CBB86018Ac2B8092FdCd39d8444aFFC3F6", "chain": "eth"},
    "Avalanche": {"address": "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7", "chain": "avalanche"},
    "Chainlink": {"address": "0x514910771AF9Ca656af840dff83E8264EcF986CA", "chain": "eth"},
}

# Moralis API base URL
MORALIS_API_URL = "https://deep-index.moralis.io/api/v2.2"


def get_moralis_api_key():
    """Get Moralis API key from environment."""
    return os.getenv("MORALIS_API_KEY")


def get_moralis_headers():
    """Get headers for Moralis API requests."""
    api_key = get_moralis_api_key()
    return {
        "Accept": "application/json",
        "X-API-Key": api_key,
    }


def get_token_holders_data(contract_address: str, chain: str = "eth"):
    """
    Get token holder data from Moralis API.
    This single endpoint returns all holder metrics including:
    - totalHolders
    - holderChange (5min, 1h, 6h, 24h, 3d, 7d, 30d)
    - holderSupply (top10, top25, top50, top100, top250, top500)
    - holderDistribution (whales, sharks, dolphins, fish, octopus, crabs, shrimps)
    - holdersByAcquisition (swap, transfer, airdrop)

    Args:
        contract_address: Token contract address
        chain: Blockchain network (eth, polygon, bsc, etc.)

    Returns:
        Dictionary with all holder data
    """
    url = f"{MORALIS_API_URL}/erc20/{contract_address}/holders?chain={chain}"

    try:
        response = requests.request("GET", url, headers=get_moralis_headers(), timeout=15)
        data = response.json()

        if response.status_code == 200:
            return data
        else:
            return {"error": data.get("message", "Unknown error")}
    except Exception as e:
        return {"error": str(e)}


def get_all_token_holders_data():
    """
    Get holder data for all configured tokens using Moralis API.

    Returns:
        Dictionary mapping token name to holder data
    """
    results = {}

    for token_name, token_info in TOKEN_CONTRACTS.items():
        contract_address = token_info["address"]
        chain = token_info.get("chain", "eth")
        try:
            # Get all holder data from single endpoint
            data = get_token_holders_data(contract_address, chain)

            if "error" in data:
                results[token_name] = {
                    "contract_address": contract_address,
                    "holder_count": None,
                    "holder_change": None,
                    "holder_supply": None,
                    "holder_distribution": None,
                    "holders_by_acquisition": None,
                    "error": data.get("error"),
                }
            else:
                results[token_name] = {
                    "contract_address": contract_address,
                    "holder_count": data.get("totalHolders"),
                    "holder_change": data.get("holderChange", {}),
                    "holder_supply": data.get("holderSupply", {}),
                    "holder_distribution": data.get("holderDistribution", {}),
                    "holders_by_acquisition": data.get("holdersByAcquisition", {}),
                }

        except Exception as e:
            results[token_name] = {
                "contract_address": contract_address,
                "holder_count": None,
                "holder_change": None,
                "holder_supply": None,
                "holder_distribution": None,
                "holders_by_acquisition": None,
                "error": str(e),
            }

    return results
