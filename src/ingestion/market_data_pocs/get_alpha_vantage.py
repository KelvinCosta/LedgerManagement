import requests
url = "https://www.alphavantage.co/query"
params = {
    "function": "GLOBAL_QUOTE",
    "symbol": "PETR4.SAO",  # PETR4 na B3
    "apikey": "SUA_CHAVE"
}
response = requests.get(url, params=params)
print(response.json())