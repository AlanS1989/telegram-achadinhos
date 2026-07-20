import requests
import json
import os
import time
import hashlib
import random
from datetime import datetime

# ============================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
# ============================================================

SHOPEE_APP_ID = "18346070306"
SHOPEE_SECRET = "YKTPIYKF4JXVZN47IDPPSG24LIFEEPWP"

# 6 horários fixos por dia
HORARIOS_CUPOM = [8, 10, 12, 15, 18, 22]

CANAIS = [
    {"canal": "@achadinhosgol01",           "nome": "Geral",       "emoji": "🛍️", "hashtags": "#achadinhos #ofertas #shopeebrasil"},
    {"canal": "@achadinhoseletronicos01",    "nome": "Eletrônicos", "emoji": "🎮", "hashtags": "#setupgamer #tecnologia #eletronicos"},
    {"canal": "@achadinhosgolddescobertas",  "nome": "Descobertas", "emoji": "🔍", "hashtags": "#achadinhosshopee #viral #gadgets"},
    {"canal": "@achadinhosgoldmoda",         "nome": "Moda",        "emoji": "💄", "hashtags": "#lookdodia #skincare #beleza"},
    {"canal": "@achadinhosgoldcasa",         "nome": "Casa",        "emoji": "🏠", "hashtags": "#donadecasa #decoracao #casainteligente"},
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
    controle = carregar_controle()
    hoje = datetime.now().strftime("%Y-%m-%d")
    chave = f"{canal}_{hora}_{hoje}"
    return controle.get(chave, False)

def marcar_postado(canal, hora):
    controle = carregar_controle()
    hoje = datetime.now().strftime("%Y-%m-%d")
    chave = f"{canal}_{hora}_{hoje}"
    controle[chave] = True
    chaves_validas = {k: v for k, v in controle.items() if hoje in k}
    salvar_controle(chaves_validas)

# ----------------------------------------------------------------
# Busca ofertas da Shopee
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

def buscar_melhor_oferta():
    """Busca a melhor oferta do momento com foto"""
    print("[Cupons] Buscando melhor oferta...")
    query = """{ productOfferV2(listType: 1, sortType: 5, limit: 30) {
        nodes {
            productName
            priceMin
            priceMax
            priceDiscountRate
            offerLink
            commissionRate
            imageUrl
            sales
            ratingStar
            shopName
        }
    } }"""
    try:
        data     = fazer_requisicao(query)
        nos      = data.get("data", {}).get("productOfferV2", {})
        produtos = nos.get("nodes", []) if nos else []

        # Filtra produtos que têm foto e desconto
        validos = [
            p for p in produtos
            if p.get("imageUrl")
            and float(p.get("priceDiscountRate", 0) or 0) > 0
            and float(p.get("priceMin", 0) or 0) > 0
        ]

        print(f"[Cupons] {len(validos)} ofertas com foto encontradas")
        return random.choice(validos) if validos else None
    except Exception as e:
        print(f"[Cupons] Erro ao buscar: {e}")
        return None

# ----------------------------------------------------------------
# Gera texto com IA (Claude API)
# ----------------------------------------------------------------
def gerar_texto_ia(produto, canal_info):
    """Usa a API do Claude para gerar um texto criativo para o post"""
    if not ANTHROPIC_API_KEY:
        return None

    nome     = str(produto.get("productName", ""))[:80]
    preco    = produto.get("priceMin", 0)
    desconto = int(float(produto.get("priceDiscountRate", 0) or 0) * 100)
    vendas   = produto.get("sales", 0)
    nota     = float(produto.get("ratingStar", 0) or 0)
    canal    = canal_info["canal"]
    emoji    = canal_info["emoji"]
    hashtags = canal_info["hashtags"]

    try:
        v = int(vendas)
        vendidos = f"{v//1000}k+ vendidos" if v >= 1000 else f"{v}+ vendidos" if v > 0 else ""
    except:
        vendidos = ""

    preco_fmt = f"R$ {float(preco):,.2f}".replace(",","X").replace(".",",").replace("X",".")

    prompt = f"""Crie um post curto e animado para um canal de ofertas no Telegram sobre este produto da Shopee:

Produto: {nome}
Preço: {preco_fmt}
Desconto: {desconto}%
Vendidos: {vendidos}
Nota: {nota}/5
Canal: {canal_info['nome']} {emoji}

Regras:
- Máximo 8 linhas
- Use emojis
- Linguagem informal e animada
- Crie urgência (sem mentir)
- NÃO inclua o link (será adicionado depois)
- NÃO inclua hashtags (serão adicionadas depois)
- NÃO inclua o nome do canal (será adicionado depois)
- Formato HTML do Telegram: use <b>negrito</b> para destacar preço e desconto
- Termine com uma chamada para ação para clicar no link abaixo"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=20
        )
        data = r.json()
        texto_ia = data.get("content", [{}])[0].get("text", "")
        if texto_ia:
            print(f"[Cupons] ✨ Texto gerado por IA")
            return texto_ia
    except Exception as e:
        print(f"[Cupons] Erro na IA: {e}")

    return None

# ----------------------------------------------------------------
# Monta o post final
# ----------------------------------------------------------------
def formatar_preco(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except:
        return "R$ --"

def montar_post(produto, canal_info, texto_ia=None):
    nome     = str(produto.get("productName", "Produto incrível"))[:80]
    preco    = produto.get("priceMin", 0)
    desconto = int(float(produto.get("priceDiscountRate", 0) or 0) * 100)
    link     = produto.get("offerLink", "https://shopee.com.br")
    nota     = float(produto.get("ratingStar", 0) or 0)
    vendas   = produto.get("sales", 0)
    canal    = canal_info["canal"]
    emoji    = canal_info["emoji"]
    hashtags = canal_info["hashtags"]

    estrelas = "⭐" * round(nota) if nota else ""
    try:
        v = int(vendas)
        vendidos = f"📦 {v//1000}k+ vendidos" if v >= 1000 else f"📦 {v}+ vendidos" if v > 0 else ""
    except:
        vendidos = ""

    if texto_ia:
        # Post com texto da IA
        corpo = texto_ia
    else:
        # Post com template padrão (fallback)
        fogo = "🔥🔥🔥" if desconto >= 60 else "🔥🔥" if desconto >= 40 else "🔥"
        corpo = f"""{fogo} <b>OFERTA IMPERDÍVEL</b> {fogo}

{emoji} {nome}

💰 Apenas <b>{formatar_preco(preco)}</b>
🏷️ <b>{desconto}% OFF</b> {estrelas}
{vendidos}"""

    post = f"""{corpo}

🛒 <a href="{link}">👉 GARANTIR ESSA OFERTA</a>

{hashtags}
📢 {canal}"""

    return post

# ----------------------------------------------------------------
# Envia foto + texto para o Telegram
# ----------------------------------------------------------------
def enviar_com_foto(texto, foto_url, canal):
    """Envia a foto do produto com o texto como legenda"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    try:
        r = requests.post(url, json={
            "chat_id":    canal,
            "photo":      foto_url,
            "caption":    texto,
            "parse_mode": "HTML",
        }, timeout=15)

        if r.status_code == 200:
            print(f"[{datetime.now().strftime('%d/%m %H:%M')}] ✅ Post com foto enviado para {canal}!")
            return True
        else:
            print(f"❌ Erro foto [{canal}]: {r.text[:100]}")
            # Tenta enviar só o texto como fallback
            return enviar_texto(texto, canal)
    except Exception as e:
        print(f"Erro ao enviar foto: {e}")
        return enviar_texto(texto, canal)

def enviar_texto(texto, canal):
    """Fallback: envia só texto se a foto falhar"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id":                  canal,
            "text":                     texto,
            "parse_mode":               "HTML",
            "disable_web_page_preview": False,
        }, timeout=10)
        if r.status_code == 200:
            print(f"[{datetime.now().strftime('%d/%m %H:%M')}] ✅ Post texto enviado para {canal}!")
            return True
        else:
            print(f"❌ Erro texto [{canal}]: {r.text[:100]}")
            return False
    except Exception as e:
        print(f"Erro ao enviar texto: {e}")
        return False

# ----------------------------------------------------------------
def verificar_e_postar_cupons():
    agora = datetime.now().hour

    if agora not in HORARIOS_CUPOM:
        return

    # Busca uma oferta com foto
    produto = buscar_melhor_oferta()
    if not produto:
        print("[Cupons] Sem ofertas com foto disponíveis.")
        return

    foto_url = produto.get("imageUrl", "")

    # Posta em cada canal
    for canal_info in CANAIS:
        canal = canal_info["canal"]

        if ja_postou_hoje(canal, agora):
            print(f"[Cupons] {canal} já recebeu cupom às {agora}h hoje.")
            continue

        # Gera texto com IA (tenta primeiro)
        texto_ia = gerar_texto_ia(produto, canal_info)

        # Monta o post
        texto = montar_post(produto, canal_info, texto_ia)

        # Envia com foto se disponível
        if foto_url:
            sucesso = enviar_com_foto(texto, foto_url, canal)
        else:
            sucesso = enviar_texto(texto, canal)

        if sucesso:
            marcar_postado(canal, agora)

        time.sleep(5)

# ----------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 55)
    print("🏷️  MÓDULO DE CUPONS COM IA + FOTO")
    print(f"⏰ Horários: {HORARIOS_CUPOM}h")
    print(f"📢 Canais: {len(CANAIS)}")
    print(f"🤖 IA: {'Ativa' if ANTHROPIC_API_KEY else 'Inativa (sem chave)'}")
    print("=" * 55)

    verificar_e_postar_cupons()

    try:
        while True:
            time.sleep(60)
            verificar_e_postar_cupons()
    except KeyboardInterrupt:
        print("\nMódulo de cupons encerrado.")
