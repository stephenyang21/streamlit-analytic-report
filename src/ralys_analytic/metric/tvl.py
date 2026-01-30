from datetime import datetime 


def getTVLChain(client,chain):
    result = client.tvl.getHistoricalChainTvl(chain)

    return result


def monthlyTVL(data):
    # Monthly average TVL
    monthly_tvl = {}
    monthly_output = []
    for item in data:
        date = datetime.fromtimestamp(item['date'])
        key = (date.year, date.month)
        if key not in monthly_tvl:
            monthly_tvl[key] = []
        monthly_tvl[key].append(item['tvl'])

    for (year, month), values in sorted(monthly_tvl.items()):
        avg = sum(values) / len(values)
        
        monthly_output.append( (f"{year}-{month:02d}", avg))
    
    return monthly_output

def annualTVL(data):

    # Annual average TVL
    annual_tvl = {}
    annual_output = []
    for item in data:
        year = datetime.fromtimestamp(item['date']).year
        if year not in annual_tvl:
            annual_tvl[year] = []
        annual_tvl[year].append(item['tvl'])

    print("\nAnnual Average TVL:")
    for year, values in sorted(annual_tvl.items()):
        avg = sum(values) / len(values)

        annual_output.append( (f"{year}", avg))

    return annual_output

def getLastestTVL(data):
    return data[-1][1]