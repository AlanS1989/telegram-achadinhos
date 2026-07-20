import requests
import json
import os
import time
import hashlib
from datetime import datetime

# ============================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
# ============================================================

SHOPEE_APP_ID = "18346070306"
SHOPEE_SECRET = "YKTPIYKF4JXVZN47IDPPSG24LIFEEPWP"

# Horários fixos para postar cupons (24h)
HORARIOS_CUPOM = [[8, 10, 12, 15, 18, 22]

CANAIS = [
    {"canal": "@achadinhosgol01",            "nome": "Geral",       "emoji": "🛍️"},
    {"canal": "@achadinhoseletronicos01",     "nome": "Eletrônicos", "emoji": "🎮"},
    {"canal": "@achadinhosgolddescobertas",   "nome": "Descobertas", "emoji": "🔍"},
    {"canal": "@achadinhosgoldmoda",          "nome": "Moda",        "emoji": "💄"},
    {"canal": "@achadinhosgoldcasa",          "nome": "Casa",        "emoji": "🏠"},
]

ARQUIVO_CONTROLE = "cupons_horario.json"

# ----------------------------------------------------------------
def carregar_controle():
    if os.path.exists(ARQUIVO_CONTROLE):
        with open(ARQUIVO_CONTROLE) as f:
            return json.load(f)
    return {}

def salvar_controle(dados):
    with open(ARQUIVO_CONTROLE, "w") as f:
        json.dump(dados, f)

def ja_postou_hoje(canal, hora):
    """Verifica se já postou nesse canal nessa hora hoje"""
    controle = carregar_controle()
    hoje = datetime.now().strftime("%Y-%m-%d")
    chave = f"{canal}_{hora}_{hoje}"
    return controle.get(chave, False)

def marcar_postado(canal, hora):
    controle = carregar_controle()
    hoje = datetime.now().strftime("%Y-%m-%d")
    chave = f"{canal}_{hora}_{hoje}"
    controle[chave] = True
    # Limpa entradas antigas (mantém só os últimos 2 dias)
    chaves_validas = {k: v for k, v in controle.items() if hoje in k}
    salvar_controle(chaves_validas)

# ----------------------------------------------------------------
# Busca campanhas/ofertas especiais da Shopee via API
# ----------------------------------------------------------------
def fazer_requisicao(query):
    url         = "https://open-api.affiliate.shopee.com.br/graphql"
    timestamp   = int(time.time())
    body        = {"query": query}
    body_string = json.dumps(body, separators=(',', ':'))
    raw         = SHOPEE_APP_ID + str(timestamp) + body_string + SHOPEE_SECRET
    signature   = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    headers     = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={SHOPEE_APP_ID}, Timestamp={timestamp}, Signature={signature}"
    }
    r = requests.post(url, data=body_string, headers=headers, timeout=15)
    return r.json()

def buscar_cupons_shopee():
    """Busca campanhas e ofertas especiais da Shopee (cupons e promoções)"""
    print("[Cupons] Buscando campanhas da Shopee...")

    # Busca ofertas com maior desconto — produtos com cupom embutido
    query = """{ productOfferV2(listType: 1, sortType: 5, limit: 20) {
        nodes {
            productName
            priceMin
            priceMax
            priceDiscountRate
            offerLink
            commissionRate
            periodStartTime
            periodEndTime
            shopName
        }
    } }"""

    try:
        data     = fazer_requisicao(query)
        nos      = data.get("data", {}).get("productOfferV2", {})
        produtos = nos.get("nodes", []) if nos else []
        print(f"[Cupons] {len(produtos)} ofertas encontradas")
        return produtos
    except Exception as e:
        print(f"[Cupons] Erro: {e}")
        return []

# ----------------------------------------------------------------
# Gerador de posts de cupom
# ----------------------------------------------------------------
def formatar_preco(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except:
        return "R$ --"

def formatar_desconto(v):
    try:
        return int(float(v) * 100)
    except:
        return 0

def gerar_post_cupom(produtos, canal_info):
    hora  = datetime.now().strftime("%H:%M")
    emoji = canal_info["emoji"]
    canal = canal_info["canal"]

    # Pega até 3 produtos com maior desconto para o post
    top3 = sorted(
        [p for p in produtos if float(p.get("priceDiscountRate", 0) or 0) > 0],
        key=lambda x: float(x.get("priceDiscountRate", 0) or 0),
        reverse=True
    )[:3]

    if not top3:
        return None

    # Monta lista de ofertas
    lista_ofertas = ""
    for p in top3:
        nome     = str(p.get("productName",""))[:50]
        preco    = p.get("priceMin", 0)
        desconto = formatar_desconto(p.get("priceDiscountRate", 0))
        link     = p.get("offerLink","https://shopee.com.br")
        lista_ofertas += f"\n🔥 <a href=\"{link}\">{nome}</a>\n   💰 {formatar_preco(preco)} | {desconto}% OFF\n"

    post = f"""🏷️ <b>CUPONS E OFERTAS DO DIA — {hora}</b> 🏷️

{emoji} Selecionamos as melhores ofertas com desconto para você agora:
{lista_ofertas}
⚡ <b>Aproveite antes de acabar o estoque!</b>

🛒 Clique nos links acima para garantir

#cupons #ofertas #shopee #desconto
📢 {canal}"""

    return post

# ----------------------------------------------------------------
def enviar(texto, canal):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id":                  canal,
            "text":                     texto,
            "parse_mode":               "HTML",
            "disable_web_page_preview": False,
        }, timeout=10)
        if r.status_code == 200:
            print(f"[{datetime.now().strftime('%d/%m %H:%M')}] ✅ Cupom enviado para {canal}!")
            return True
        else:
            print(f"❌ Erro [{canal}]: {r.text}")
            return False
    except Exception as e:
        print(f"Erro ao enviar: {e}")
        return False

# ----------------------------------------------------------------
def verificar_e_postar_cupons():
    agora = datetime.now().hour

    # Só roda nos horários fixos definidos
    if agora not in HORARIOS_CUPOM:
        return

    # Busca os produtos/cupons uma vez
    produtos = buscar_cupons_shopee()
    if not produtos:
        print("[Cupons] Sem ofertas disponíveis no momento.")
        return

    # Posta em cada canal se ainda não postou nessa hora
    for canal_info in CANAIS:
        canal = canal_info["canal"]
        if ja_postou_hoje(canal, agora):
            print(f"[Cupons] {canal} já recebeu cupom às {agora}h hoje.")
            continue

        texto = gerar_post_cupom(produtos, canal_info)
        if not texto:
            continue

        if enviar(texto, canal):
            marcar_postado(canal, agora)

        time.sleep(5)  # pausa entre canais

# ----------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 55)
    print("🏷️  MÓDULO DE CUPONS INICIADO")
    print(f"⏰ Horários fixos: {HORARIOS_CUPOM}h")
    print(f"📢 Canais: {len(CANAIS)}")
    print("=" * 55)

    verificar_e_postar_cupons()

    try:
        while True:
            time.sleep(60)  # verifica a cada 1 minuto
            verificar_e_postar_cupons()
    except KeyboardInterrupt:
        print("\nMódulo de cupons encerrado.")
