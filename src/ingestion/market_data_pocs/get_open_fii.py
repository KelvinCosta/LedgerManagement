import requests
from bs4 import BeautifulSoup
response = requests.get("https://fiis.com.br/lista-de-fundos-imobiliarios/")
# Extrair dados com BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")
with open("fiis.html", "w") as file:
    file.write(str(soup))