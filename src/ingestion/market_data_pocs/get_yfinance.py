import yfinance as yf
petr4 = yf.Ticker("PETR4.SA")
historico = petr4.history(period="1y")
dividendos = petr4.dividends
print(historico)