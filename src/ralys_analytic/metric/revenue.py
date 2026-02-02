from datetime import datetime


def getRevenueByChain(client, chain):
    chain_string = chain.lower().replace(" ", "_")
    result = client.fees.getOverviewByChain(chain_string)
    return result['totalDataChart']

def getRevenueByProtocol(client,protocol):
    protocol_string = protocol.lower().replace(" ", "_")
    result = client.fees.getSummary(protocol_string)
    return result['totalDataChart']


def monthlyRevenue(data):
    # Monthly total revenue
    monthly_revenue = {}
    monthly_output = []
    for item in data:
        date = datetime.fromtimestamp(item[0])
        key = (date.year, date.month)
        if key not in monthly_revenue:
            monthly_revenue[key] = 0
        monthly_revenue[key] += item[1]

    for (year, month), total in sorted(monthly_revenue.items()):
        monthly_output.append((f"{year}-{month:02d}", total))

    return monthly_output


def annualRevenue(data):
    # Annual total revenue
    annual_revenue = {}
    annual_output = []
    for item in data:
        year = datetime.fromtimestamp(item[0]).year
        if year not in annual_revenue:
            annual_revenue[year] = 0
        annual_revenue[year] += item[1]

    for year, total in sorted(annual_revenue.items()):
        annual_output.append((f"{year}", total))

    return annual_output


def getLatestRevenue(data):
    return data[-1][1]


def getRevenueGrowth(data, days=30):
    """
    Calculate revenue growth rate over a specified number of days.

    Args:
        data: List of [timestamp, revenue] pairs
        days: Number of days to calculate growth over (30 or 90)

    Returns:
        Growth rate as a percentage, or None if insufficient data
    """
    if not data or len(data) < 2:
        return None

    # Sort by timestamp
    sorted_data = sorted(data, key=lambda x: x[0])

    # Get the latest timestamp
    latest_ts = sorted_data[-1][0]
    target_ts = latest_ts - (days * 24 * 60 * 60)

    # Find the data point closest to target_ts
    past_revenue = None
    for item in sorted_data:
        if item[0] <= target_ts:
            past_revenue = item[1]
        else:
            break

    if past_revenue is None or past_revenue == 0:
        # Try to get the earliest available data point
        if len(sorted_data) > 1:
            past_revenue = sorted_data[0][1]
        else:
            return None

    # Calculate cumulative revenue for the periods
    # Sum revenue for the last N days
    current_period_revenue = sum(
        item[1] for item in sorted_data
        if item[0] > latest_ts - (days * 24 * 60 * 60)
    )

    # Sum revenue for the previous N days
    previous_period_revenue = sum(
        item[1] for item in sorted_data
        if latest_ts - (2 * days * 24 * 60 * 60) < item[0] <= latest_ts - (days * 24 * 60 * 60)
    )

    if previous_period_revenue == 0:
        return None

    growth_rate = ((current_period_revenue - previous_period_revenue) / previous_period_revenue) * 100
    return growth_rate
