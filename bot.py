import requests
import json
import os
import random
import time
import hashlib
from datetime import datetime
import threading

# ============================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
# ============================================================

SHOPEE_APP_ID  = "18346070306"
SHOPEE_SECRET  = "YKTPIYKF4JXVZN47IDPPSG24LIFEEPWP"

HORA_INICIO   = 7
HORA_FIM      = 23
POSTS_POR_DIA = 30
INTERVALO     = (HORA_FIM - HORA_INICIO) * 3600 // POSTS_POR_DIA  # ~32 min

# ============================================================
# NICHOS — canal + keywords + emoji + nome
# ============================================================
NICHOS = [
    {
        "id":      "geral",
        "canal":   "@achadinhosgol01",
        "nome":    "Achadinhos Geral",
        "emoji":   "🛍️",
        "arquivo": "usados_geral.json",
        "keywords": [
            "oferta do dia", "mais vendido", "promoção",
            "fone bluetooth", "tenis", "relogio smartwatch",
            "mochila", "camisa", "celular", "notebook",
            "perfume", "kit maquiagem", "air fryer", "panela",
            "brinquedo", "jogo", "ferramenta", "camera", "tablet",
        ],
    },
    {
        "id":      "eletronicos",
        "canal":   "@achadinhoseletronicos01",
        "nome":    "Games e Eletrônicos",
        "emoji":   "🎮",
        "arquivo": "usados_eletronicos.json",
        "keywords": [
            "fone bluetooth", "celular", "notebook", "tablet",
            "mouse gamer", "teclado gamer", "headset gamer",
            "monitor", "ssd externo", "pendrive", "carregador",
            "cabo usb", "controle xbox", "controle playstation",
            "placa de video", "processador", "memória ram",
            "câmera fotográfica", "drone", "smartwatch",
        ],
    },
    {
        "id":      "descobertas",
        "canal":   "@achadinhosgolddescobertas",
        "nome":    "Descobertas do Dia",
        "emoji":   "🔍",
        "arquivo": "usados_descobertas.json",
        "keywords": [
            "produto inusitado", "gadget", "novidade",
            "produto viral", "produto tiktok", "mini",
            "portátil", "multifuncional", "kit completo",
            "combo", "conjunto", "coleção", "lançamento",
            "produto japonês", "produto importado",
            "acessório criativo", "utensílio inteligente",
            "organizador", "suporte", "adaptador",
        ],
    },
    {
        "id":      "moda",
        "canal":   "@achadinhosgoldmoda",
        "nome":    "Beleza e Moda",
        "emoji":   "💄",
        "arquivo": "usados_moda.json",
        "keywords": [
            "perfume feminino", "kit maquiagem feminino", "batom",
            "base maquiagem", "paleta de sombra", "delineador",
            "rímel", "blush", "iluminador maquiagem", "pincel maquiagem",
            "skincare feminino", "sérum facial feminino", "creme antirrugas",
            "protetor solar facial feminino", "máscara facial feminina",
            "vestido feminino", "blusa feminina", "calça jeans feminina",
            "saia feminina", "conjunto feminino", "macacão feminino",
            "tênis feminino", "sandália feminina", "bolsa feminina",
            "brinco feminino", "colar feminino", "óculos de sol feminino",
            "esmalte", "secador de cabelo feminino", "chapinha cabelo",
            "lingerie", "biquíni", "conjunto fitness feminino",
        ],
    },
    {
        "id":      "casa",
        "canal":   "@achadinhosgoldcasa",
        "nome":    "Casa e Utilidades",
        "emoji":   "🏠",
        "arquivo": "usados_casa.json",
        "keywords": [
            "air fryer", "panela pressão", "liquidificador",
            "cafeteira", "fritadeira elétrica", "aspirador de pó",
            "ventilador", "jogo de cama", "toalha de banho",
            "tapete sala", "organizador", "rack tv",
            "luminaria led", "churrasqueira elétrica", "forno elétrico",
            "batedeira", "sanduicheira", "ferro de passar",
            "jogo de panelas", "cortina blackout", "almofada",
            "espelho decorativo", "suporte tv parede",
        ],
    },
]

# ----------------------------------------------------------------
def carregar_usados(arquivo):
    if os.path.exists(arquivo):
        with open(arquivo) as f:
            return json.load(f)
    return []

def salvar_usados(arquivo, lista):
    with open(arquivo, "w") as f:
        json.dump(lista[-500:], f)

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

def buscar_produtos(nicho):
    keyword = random.choice(nicho["keywords"])
    print(f"[{nicho['nome']}] Buscando: '{keyword}'")
    query = f'{{ productOfferV2(keyword: "{keyword}", sortType: 2, limit: 50) {{ nodes {{ productName priceMin priceDiscountRate ratingStar offerLink commissionRate sales }} }} }}'
    try:
        data     = fazer_requisicao(query)
        nos      = data.get("data", {}).get("productOfferV2", {})
        produtos = nos.get("nodes", []) if nos else []
        print(f"[{nicho['nome']}] {len(produtos)} produtos encontrados")
        return produtos
    except Exception as e:
        print(f"[{nicho['nome']}] Erro: {e}")
        return []

# ----------------------------------------------------------------
def formatar_preco(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except:
        return "R$ --"

def formatar_vendas(v):
    try:
        v = int(v)
        if v >= 1000:
            return f"{v//1000}k+ vendidos"
        return f"{v}+ vendidos"
    except:
        return ""

def gerar_post(p, nicho):
    nome     = str(p.get("productName","Produto incrível"))[:80]
    preco    = p.get("priceMin", 0)
    desconto = int(float(p.get("priceDiscountRate", 0) or 0) * 100)
    nota     = float(p.get("ratingStar", 0) or 0)
    link     = p.get("offerLink","https://shopee.com.br")
    vendas   = formatar_vendas(p.get("sales", 0))
    estrelas = "⭐" * round(nota) if nota else ""
    fogo     = "🔥🔥🔥" if desconto >= 60 else "🔥🔥" if desconto >= 40 else "🔥"
    emoji    = nicho["emoji"]
    canal    = nicho["canal"]
    hora     = datetime.now().strftime("%H:%M")

    templates = [
        f"""{fogo} <b>ACHADINHO DO DIA</b> {fogo}

{emoji} {nome}

💰 Apenas <b>{formatar_preco(preco)}</b>
🏷️ <b>{desconto}% OFF</b> {estrelas}
📦 {vendas}

🛒 <a href="{link}">👉 COMPRAR AGORA</a>

💬 Manda pra quem tá precisando!
📢 {canal}""",

        f"""{emoji} <b>OFERTA RELÂMPAGO — {hora}</b> {emoji}

👉 <b>{nome}</b>

📦 {vendas}
💵 <b>{formatar_preco(preco)}</b>
📉 <b>{desconto}% OFF</b> {estrelas}

🔗 <a href="{link}">GARANTIR OFERTA</a>

⏰ Corre antes de acabar!
📢 {canal}""",

        f"""💥 <b>NÃO PERCA ESSA OFERTA!</b> 💥

{emoji} {nome}

📦 {vendas}
💵 <b>{formatar_preco(preco)}</b> ({desconto}% OFF)
{estrelas}

🛒 <a href="{link}">Comprar na Shopee</a>

📲 Compartilha com seus amigos!
📢 {canal}""",

        f"""🎯 <b>MAIS VENDIDO DO DIA</b>

{fogo} {nome}

📦 {vendas}
Por apenas <b>{formatar_preco(preco)}</b>
🏷️ <b>{desconto}% OFF</b> {estrelas}

👇 <a href="{link}">APROVEITAR AGORA</a>

💡 Siga para mais achadinhos!
📢 {canal}""",
    ]
    return random.choice(templates)

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
            return True
        else:
            print(f"❌ Erro Telegram [{canal}]: {r.text}")
            return False
    except Exception as e:
        print(f"Erro ao enviar [{canal}]: {e}")
        return False

# ----------------------------------------------------------------
def postar_nicho(nicho):
    agora = datetime.now().hour
    if agora < HORA_INICIO or agora >= HORA_FIM:
        return

    usados   = carregar_usados(nicho["arquivo"])
    produtos = buscar_produtos(nicho)

    if not produtos:
        return

    filtrados = [
        p for p in produtos
        if p.get("productName","") not in usados
        and float(p.get("priceMin") or 0) > 0
    ]
    if not filtrados:
        usados    = []
        filtrados = [p for p in produtos if float(p.get("priceMin") or 0) > 0]

    if not filtrados:
        return

    produto = random.choice(filtrados)
    texto   = gerar_post(produto, nicho)

    if enviar(texto, nicho["canal"]):
        print(f"[{datetime.now().strftime('%d/%m %H:%M')}] ✅ [{nicho['nome']}] Post enviado!")
        usados.append(produto.get("productName",""))
        salvar_usados(nicho["arquivo"], usados)

def postar_todos():
    """Posta em todos os nichos com 30s de intervalo entre cada um"""
    for nicho in NICHOS:
        try:
            postar_nicho(nicho)
        except Exception as e:
            print(f"Erro no nicho {nicho['nome']}: {e}")
        time.sleep(30)  # 30s entre cada canal para não sobrecarregar a API

# ----------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 55)
    print("🤖 BOT ACHADINHOS — 5 NICHOS")
    print(f"📅 {POSTS_POR_DIA} posts/dia por canal | {HORA_INICIO}h às {HORA_FIM}h")
    print(f"⏱️  Ciclo a cada {INTERVALO}s (~{INTERVALO//60} min)")
    print("📢 Canais:")
    for n in NICHOS:
        print(f"   {n['emoji']}  {n['canal']}")
    print("=" * 55)

    postar_todos()  # dispara imediatamente ao iniciar

    try:
        while True:
            time.sleep(INTERVALO)
            postar_todos()
    except KeyboardInterrupt:
        print("\nBot encerrado.")
