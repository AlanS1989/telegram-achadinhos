import requests
import json
import os
import random
import time
import hashlib
from datetime import datetime
from threading import Thread
from keep_alive import keep_alive

keep_alive()

# ============================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
# ============================================================

SHOPEE_APP_ID  = "18346070306"
SHOPEE_SECRET  = "YKTPIYKF4JXVZN47IDPPSG24LIFEEPWP"

POSTS_POR_DIA  = 110
HORA_INICIO    = 7
HORA_FIM       = 23
INTERVALO      = (HORA_FIM - HORA_INICIO) * 3600 // POSTS_POR_DIA  # ~524s (~8 min)

# Horários fixos para cupons
HORARIOS_CUPOM = [8, 10, 12, 15, 18, 22]
ARQUIVO_CONTROLE_CUPOM = "cupons_horario.json"

# ============================================================
# NICHOS
# ============================================================
NICHOS = [
    {
        "id":      "geral",
        "canal":   "@achadinhosgol01",
        "nome":    "Achadinhos Geral",
        "emoji":   "🛍️",
        "arquivo": "usados_geral.json",
        "hashtags": "#achadinhos #ofertas #shopeebrasil",
        "keywords": [
            "oferta relâmpago", "mais vendidos", "frete grátis", "smartwatch",
            "fone bluetooth", "air fryer", "kit maquiagem", "mochila",
            "smartphone", "tênis", "luminária", "smart tv", "ventilador",
            "caixa de som", "kit ferramentas", "garrafa térmica",
            "relógio masculino", "fone sem fio", "óculos", "bolsa",
            "carregador", "chinelo nuvem", "garrafa de água", "guarda chuva",
            "meia", "boné", "carteira", "kit cueca", "relógio digital",
            "câmera de segurança", "ring light", "tapete", "garrafa motivacional",
            "umidificador", "mini processador"
        ],
    },
    {
        "id":      "eletronicos",
        "canal":   "@achadinhoseletronicos01",
        "nome":    "Games e Eletrônicos",
        "emoji":   "🎮",
        "arquivo": "usados_eletronicos.json",
        "hashtags": "#setupgamer #tecnologia #eletronicos",
        "keywords": [
            "fone gamer", "alexa", "smartwatch", "teclado mecânico",
            "mouse sem fio", "powerbank", "ssd", "ring light",
            "carregador turbo", "xiaomi", "caixa de som", "monitor gamer",
            "cabo iphone", "suporte celular", "microfone", "impressora",
            "hub usb", "webcam", "controle ps4", "fone de ouvido jbl",
            "fita led", "cabo tipo c", "pendrive", "cartão de memória",
            "tv box", "controle pc", "fone de ouvido bluetooth",
            "placa de vídeo", "processador", "cooler", "gabinete gamer",
            "mousepad gamer", "roteador", "adaptador bluetooth", "carregador portátil"
        ],
    },
    {
        "id":      "descobertas",
        "canal":   "@achadinhosgolddescobertas",
        "nome":    "Descobertas do Dia",
        "emoji":   "🔍",
        "arquivo": "usados_descobertas.json",
        "hashtags": "#achadinhosshopee #viral #gadgets",
        "keywords": [
            "viral tiktok", "mini projetor", "umidificador", "led rgb",
            "organizador criativo", "garrafa térmica", "mini liquidificador",
            "utilidade inteligente", "fofo", "estético", "fita led",
            "luminária 3d", "projetor galáxia", "massageador", "caneca térmica",
            "lixeira inteligente", "suporte notebook", "mini impressora",
            "seladora de embalagem", "abridor de vinho elétrico", "escova secadora",
            "mini ventilador", "dispenser pasta de dente", "removedor de pelos",
            "mop giratório", "saboneteira automática", "triturador alho elétrico",
            "fone invisível", "óculos inteligente", "lancheira elétrica",
            "capa impermeável celular", "luz de armário", "balança digital",
            "mini geladeira", "depilador a laser"
        ],
    },
    {
        "id":      "moda",
        "canal":   "@achadinhosgoldmoda",
        "nome":    "Beleza e Moda",
        "emoji":   "💄",
        "arquivo": "usados_moda.json",
        "hashtags": "#lookdodia #skincare #beleza",
        "keywords": [
            "skincare", "kit maquiagem", "perfume", "bolsa feminina",
            "conjunto", "tênis casual", "secador de cabelo", "óculos de sol",
            "moda fitness", "relógio feminino", "prata 925", "mochila feminina",
            "bota", "vestido longo", "pincel de maquiagem", "jaqueta",
            "acessórios cabelo", "body", "saia", "cropped", "batom líquido",
            "base matte", "delineador", "paleta de sombras", "blush",
            "rímel", "cílios postiços", "esponja maquiagem", "protetor solar facial",
            "sérum vitamina c", "chapinha", "babyliss", "biquíni", "pijama",
            "calça pantalona"
        ],
    },
    {
        "id":      "casa",
        "canal":   "@achadinhosgoldcasa",
        "nome":    "Casa e Utilidades",
        "emoji":   "🏠",
        "arquivo": "usados_casa.json",
        "hashtags": "#donadecasa #decoracao #casainteligente",
        "keywords": [
            "air fryer", "aspirador robô", "liquidificador", "jogo de lençol",
            "organizador", "cafeteira", "espelho decorativo", "kit potes",
            "panela de pressão", "mop", "toalha de banho", "pote de vidro",
            "faqueiro", "toalha de mesa", "varal", "cabide veludo",
            "manta", "travesseiro", "papel de parede", "tapete sala",
            "jogo de cama", "cortina", "almofada", "quadro decorativo",
            "prateleira", "sapateira", "cesto de roupa", "escorredor de louça",
            "jogo de panelas", "batedeira", "chaleira elétrica", "frigideira antiaderente",
            "aparelho de jantar", "lixeira inox", "dispenser sabão"
        ],
    },
]

# ============================================================
# FUNÇÕES GERAIS
# ============================================================
def carregar_usados(arquivo):
    if os.path.exists(arquivo):
        with open(arquivo) as f:
            return json.load(f)
    return []

def salvar_usados(arquivo, lista):
    with open(arquivo, "w") as f:
        json.dump(lista[-500:], f)

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
        return f"{v}+ vendidos" if v > 0 else ""
    except:
        return ""

# ============================================================
# MÓDULO DE PRODUTOS (loop principal)
# ============================================================
def buscar_produtos(nicho):
    keyword = random.choice(nicho["keywords"])
    print(f"[{nicho['nome']}] Buscando: '{keyword}'")
    query = f'{{ productOfferV2(keyword: "{keyword}", sortType: 2, limit: 50) {{ nodes {{ productName priceMin priceDiscountRate ratingStar offerLink commissionRate sales }} }} }}'
    try:
        data     = fazer_requisicao(query)
        nos      = data.get("data", {}).get("productOfferV2", {})
        produtos = nos.get("nodes", []) if nos else []
        print(f"[{nicho['nome']}] {len(produtos)} produtos")
        return produtos
    except Exception as e:
        print(f"[{nicho['nome']}] Erro: {e}")
        return []

def gerar_post_produto(p, nicho):
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
    hashtags = nicho["hashtags"]
    hora     = datetime.now().strftime("%H:%M")

    templates = [
        f"""{fogo} <b>ACHADINHO DO DIA</b> {fogo}

{emoji} {nome}

💰 Apenas <b>{formatar_preco(preco)}</b>
🏷️ <b>{desconto}% OFF</b> {estrelas}
📦 {vendas}

🛒 <a href="{link}">👉 COMPRAR AGORA</a>

💬 Manda pra quem tá precisando!
{hashtags}
📢 {canal}""",

        f"""{emoji} <b>OFERTA RELÂMPAGO — {hora}</b> {emoji}

👉 <b>{nome}</b>

📦 {vendas}
💵 <b>{formatar_preco(preco)}</b>
📉 <b>{desconto}% OFF</b> {estrelas}

🔗 <a href="{link}">GARANTIR OFERTA</a>

⏰ Corre antes de acabar!
{hashtags}
📢 {canal}""",

        f"""💥 <b>NÃO PERCA ESSA OFERTA!</b> 💥

{emoji} {nome}

📦 {vendas}
💵 <b>{formatar_preco(preco)}</b> ({desconto}% OFF)
{estrelas}

🛒 <a href="{link}">Comprar na Shopee</a>

📲 Compartilha com seus amigos!
{hashtags}
📢 {canal}""",

        f"""🎯 <b>MAIS VENDIDO DO DIA</b>

{fogo} {nome}

📦 {vendas}
Por apenas <b>{formatar_preco(preco)}</b>
🏷️ <b>{desconto}% OFF</b> {estrelas}

👇 <a href="{link}">APROVEITAR AGORA</a>

💡 Siga para mais achadinhos!
{hashtags}
📢 {canal}""",
    ]
    return random.choice(templates)

def enviar_mensagem(texto, canal):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id":                  canal,
            "text":                     texto,
            "parse_mode":               "HTML",
            "disable_web_page_preview": False,
        }, timeout=10)
        return r.status_code == 200
    except:
        return False

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
    texto   = gerar_post_produto(produto, nicho)

    if enviar_mensagem(texto, nicho["canal"]):
        print(f"[{datetime.now().strftime('%d/%m %H:%M')}] ✅ [{nicho['nome']}] Post enviado!")
        usados.append(produto.get("productName",""))
        salvar_usados(nicho["arquivo"], usados)

def postar_todos():
    for nicho in NICHOS:
        try:
            postar_nicho(nicho)
        except Exception as e:
            print(f"Erro no nicho {nicho['nome']}: {e}")
        time.sleep(15)

# ============================================================
# MÓDULO DE CUPONS (thread paralela)
# ============================================================
def carregar_controle_cupom():
    if os.path.exists(ARQUIVO_CONTROLE_CUPOM):
        with open(ARQUIVO_CONTROLE_CUPOM) as f:
            return json.load(f)
    return {}

def salvar_controle_cupom(dados):
    with open(ARQUIVO_CONTROLE_CUPOM, "w") as f:
        json.dump(dados, f)

def ja_postou_cupom(canal, hora):
    controle = carregar_controle_cupom()
    hoje = datetime.now().strftime("%Y-%m-%d")
    return controle.get(f"{canal}_{hora}_{hoje}", False)

def marcar_cupom_postado(canal, hora):
    controle = carregar_controle_cupom()
    hoje = datetime.now().strftime("%Y-%m-%d")
    controle[f"{canal}_{hora}_{hoje}"] = True
    chaves_validas = {k: v for k, v in controle.items() if hoje in k}
    salvar_controle_cupom(chaves_validas)

def buscar_ofertas_cupom():
    print("[Cupons] Buscando melhores ofertas...")
    query = """{ productOfferV2(listType: 1, sortType: 5, limit: 30) {
        nodes {
            productName priceMin priceDiscountRate
            offerLink imageUrl sales ratingStar
        }
    } }"""
    try:
        data     = fazer_requisicao(query)
        nos      = data.get("data", {}).get("productOfferV2", {})
        produtos = nos.get("nodes", []) if nos else []
        validos  = [
            p for p in produtos
            if float(p.get("priceDiscountRate", 0) or 0) > 0
            and float(p.get("priceMin", 0) or 0) > 0
        ]
        print(f"[Cupons] {len(validos)} ofertas encontradas")
        return validos
    except Exception as e:
        print(f"[Cupons] Erro: {e}")
        return []

def gerar_post_cupom(produtos, canal_info):
    emoji    = canal_info["emoji"]
    canal    = canal_info["canal"]
    hashtags = canal_info["hashtags"]
    hora     = datetime.now().strftime("%H:%M")

    top3 = sorted(
        produtos,
        key=lambda x: float(x.get("priceDiscountRate", 0) or 0),
        reverse=True
    )[:3]

    if not top3:
        return None

    lista = ""
    for p in top3:
        nome     = str(p.get("productName",""))[:50]
        preco    = formatar_preco(p.get("priceMin", 0))
        desconto = int(float(p.get("priceDiscountRate", 0) or 0) * 100)
        link     = p.get("offerLink","https://shopee.com.br")
        lista   += f"\n🔥 <a href=\"{link}\">{nome}</a>\n   💰 {preco} | {desconto}% OFF\n"

    return f"""🏷️ <b>CUPONS E OFERTAS — {hora}</b> 🏷️

{emoji} Selecionamos as melhores ofertas com desconto agora:
{lista}
⚡ <b>Aproveite antes de acabar!</b>

{hashtags}
📢 {canal}"""

def enviar_cupom_com_foto(texto, foto_url, canal):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    try:
        r = requests.post(url, json={
            "chat_id":    canal,
            "photo":      foto_url,
            "caption":    texto,
            "parse_mode": "HTML",
        }, timeout=15)
        if r.status_code == 200:
            return True
        # Fallback sem foto
        return enviar_mensagem(texto, canal)
    except:
        return enviar_mensagem(texto, canal)

def verificar_e_postar_cupons():
    agora = datetime.now().hour
    if agora not in HORARIOS_CUPOM:
        return

    produtos = buscar_ofertas_cupom()
    if not produtos:
        return

    foto_url = produtos[0].get("imageUrl", "") if produtos else ""

    for canal_info in NICHOS:
        canal = canal_info["canal"]
        if ja_postou_cupom(canal, agora):
            continue

        texto = gerar_post_cupom(produtos, canal_info)
        if not texto:
            continue

        if foto_url:
            sucesso = enviar_cupom_com_foto(texto, foto_url, canal)
        else:
            sucesso = enviar_mensagem(texto, canal)

        if sucesso:
            print(f"[{datetime.now().strftime('%d/%m %H:%M')}] 🏷️ Cupom enviado para {canal}!")
            marcar_cupom_postado(canal, agora)

        time.sleep(5)

def loop_cupons():
    while True:
        try:
            verificar_e_postar_cupons()
        except Exception as e:
            print(f"[Cupons] Erro no loop: {e}")
        time.sleep(60)

# ============================================================
# INICIALIZAÇÃO
# ============================================================
if __name__ == "__main__":
    print("=" * 55)
    print("🤖 ACHADINHOBOT — 5 NICHOS + CUPONS")
    print(f"📅 {POSTS_POR_DIA} posts/dia por canal | {HORA_INICIO}h às {HORA_FIM}h")
    print(f"⏱️  1 post a cada {INTERVALO}s (~{INTERVALO//60} min)")
    print(f"🏷️  Cupons nos horários: {HORARIOS_CUPOM}h")
    print("📢 Canais:")
    for n in NICHOS:
        print(f"   {n['emoji']}  {n['canal']}")
    print("=" * 55)

    # Inicia o módulo de cupons em thread paralela
    Thread(target=loop_cupons, daemon=True).start()
    print("🏷️  Módulo de cupons ativo!")

    # Loop principal de produtos
    postar_todos()

    try:
        while True:
            time.sleep(INTERVALO)
            postar_todos()
    except KeyboardInterrupt:
        print("\nBot encerrado.")
