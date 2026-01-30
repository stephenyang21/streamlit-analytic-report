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
