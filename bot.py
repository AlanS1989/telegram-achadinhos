import requests
import pandas as pd

TOKEN = "7757684344:AAHpaypxmjKTsDNRw9z--wvHwmPFoTu5QQI"

CHAT_ID = "@achadinhosgolden01"

sheet_id = "11CUjrM-7qra8TL84gleA5ns66UHR1FFIDOifWWxsoXY"

url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

df = pd.read_csv(url)

for _, row in df.iterrows():

    mensagem = f"""
🔥 ACHADINHO DO DIA

🛍 Produto: {row['Produto']}

💰 Preço: {row['Preço']}

🛒 Comprar:
{row['Link']}

⚡ Oferta por tempo limitado
"""

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": mensagem
        }
    )
