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
# ATENÇÃO: mova essas duas credenciais para variáveis de ambiente
# (igual foi feito com TELEGRAM_TOKEN) antes de compartilhar/publicar
# este código em qualquer lugar. Deixá-las no código é um risco de
# segurança real: quem tiver acesso ao arquivo tem acesso à sua conta
# de afiliado Shopee.
SHOPEE_APP_ID  = os.environ.get("SHOPEE_APP_ID", "18346070306")
SHOPEE_SECRET  = os.environ.get("SHOPEE_SECRET", "YKTPIYKF4JXVZN47IDPPSG24LIFEEPWP")

POSTS_POR_DIA  = 200
HORA_INICIO    = 7
HORA_FIM       = 23
INTERVALO      = (HORA_FIM - HORA_INICIO) * 3600 // POSTS_POR_DIA  # ~4-5 min

# Horários fixos para o cupom geral do app
HORARIOS_CUPOM = [8, 10, 12, 15, 18, 22]
ARQUIVO_CONTROLE_CUPOM = "cupons_horario.json"

# Horários fixos para os posts de "Recomendados do Dia" (intercalados com cupom)
HORARIOS_RECOMENDADOS = [9, 13, 17, 21]
ARQUIVO_CONTROLE_RECOMENDADOS = "recomendados_horario.json"

# ============================================================
# CUPONS GERAIS SHOPEE (cupom de carrinho, não é por produto)
# Atualize esta lista manualmente sempre que a Shopee mudar os valores/link.
# ============================================================
CUPONS_ATIVOS = [
    {"desconto": "R$30 OFF", "condicao": "em compras acima de R$299"},
    {"desconto": "R$90 OFF", "condicao": "em compras acima de R$899"},
]
LINK_CUPONS = "https://s.shopee.com.br/8Ko5h7hrcP"

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

def gerar_link_afiliado(url_original, sub_ids=None):
    """
    Converte qualquer link Shopee em um link afiliado rastreado pela SUA conta
    (usa o mesmo SHOPEE_APP_ID/SHOPEE_SECRET já usado nas outras chamadas).
    Comissão é gerada em cima de qualquer compra feita após o clique, dentro
    da janela de atribuição da Shopee — não só no item do link.
    sub_ids: lista de até 5 strings curtas pra identificar a origem do clique
             (ex: id do canal) nos relatórios de conversão.
    """
    sub_ids = sub_ids or []
    sub_ids_json = json.dumps(sub_ids[:5])
    mutation = (
        'mutation{ generateShortLink(input:{originUrl:"%s", subIds:%s}){ shortLink } }'
        % (url_original, sub_ids_json)
    )
    try:
        data = fazer_requisicao(mutation)
        if "errors" in data:
            print(f"[Link Afiliado] Erro da API: {data['errors']}")
            return url_original
        link = data.get("data", {}).get("generateShortLink", {}).get("shortLink")
        return link or url_original
    except Exception as e:
        print(f"[Link Afiliado] Erro: {e}")
        return url_original

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
# CONTROLE DE HORÁRIOS (usado por cupom e recomendados)
# ============================================================
def carregar_controle(arquivo):
    if os.path.exists(arquivo):
        with open(arquivo) as f:
            return json.load(f)
    return {}

def salvar_controle(arquivo, dados):
    with open(arquivo, "w") as f:
        json.dump(dados, f)

def ja_postou(arquivo, canal, hora):
    controle = carregar_controle(arquivo)
    hoje = datetime.now().strftime("%Y-%m-%d")
    return controle.get(f"{canal}_{hora}_{hoje}", False)

def marcar_postado(arquivo, canal, hora):
    controle = carregar_controle(arquivo)
    hoje = datetime.now().strftime("%Y-%m-%d")
    controle[f"{canal}_{hora}_{hoje}"] = True
    chaves_validas = {k: v for k, v in controle.items() if hoje in k}
    salvar_controle(arquivo, chaves_validas)

# ============================================================
# MÓDULO DE PRODUTOS (loop principal)
# ============================================================
def buscar_produtos(nicho):
    keyword = random.choice(nicho["keywords"])
    print(f"[{nicho['nome']}] Buscando: '{keyword}'")
    query = f'{{ productOfferV2(keyword: "{keyword}", sortType: 2, limit: 50) {{ nodes {{ productName priceMin priceDiscountRate ratingStar offerLink commissionRate sales }} }} }}'
    try:
        data = fazer_requisicao(query)
        if "errors" in data:
            print(f"[{nicho['nome']}] Erro da API: {data['errors']}")
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

def enviar_mensagem_markdown(texto, canal):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id":                  canal,
            "text":                     texto,
            "parse_mode":               "Markdown",
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
# MÓDULO DE CUPOM GERAL (thread paralela)
# Cupom fixo de carrinho — não vem da API de produtos, é editado manualmente
# na lista CUPONS_ATIVOS lá em cima.
# ============================================================
def gerar_post_cupom_geral(link):
    linhas = "\n\n".join(f"🏷️ *{c['desconto']} {c['condicao']}*" for c in CUPONS_ATIVOS)
    return f"""🚨 *CUPONS SHOPEE* 🚨

{linhas}

✅ *Válido em todo app*

🔗 *Pega aqui os CUPONS*
{link}"""

def verificar_e_postar_cupons():
    agora = datetime.now().hour
    if agora not in HORARIOS_CUPOM:
        return

    for canal_info in NICHOS:
        canal = canal_info["canal"]
        if ja_postou(ARQUIVO_CONTROLE_CUPOM, canal, agora):
            continue

        # link gerado com a SUA conta de afiliado, com sub_id do canal pra
        # você conseguir ver no relatório de conversão de onde veio cada venda
        link  = gerar_link_afiliado(LINK_CUPONS, sub_ids=[canal_info["id"], "cupom"])
        texto = gerar_post_cupom_geral(link)

        if enviar_mensagem_markdown(texto, canal):
            print(f"[{datetime.now().strftime('%d/%m %H:%M')}] 🏷️ Cupom enviado para {canal}!")
            marcar_postado(ARQUIVO_CONTROLE_CUPOM, canal, agora)

        time.sleep(5)

# ============================================================
# MÓDULO DE RECOMENDADOS (thread paralela)
# Busca em várias keywords do nicho e escolhe os 3 melhores por
# vendas + avaliação, publicando um post curado por canal.
# ============================================================
def buscar_recomendados(nicho, amostra=5):
    candidatos = []
    keywords_amostra = random.sample(nicho["keywords"], min(amostra, len(nicho["keywords"])))
    for kw in keywords_amostra:
        query = f'{{ productOfferV2(keyword: "{kw}", sortType: 2, limit: 20) {{ nodes {{ productName priceMin priceDiscountRate ratingStar offerLink commissionRate sales }} }} }}'
        try:
            data = fazer_requisicao(query)
            if "errors" in data:
                print(f"[Recomendados-{nicho['nome']}] Erro da API p/ '{kw}': {data['errors']}")
                continue
            nos      = data.get("data", {}).get("productOfferV2", {})
            produtos = nos.get("nodes", []) if nos else []
            candidatos.extend(produtos)
        except Exception as e:
            print(f"[Recomendados-{nicho['nome']}] Erro: {e}")
        time.sleep(1)  # evita bater rate limit da API
    return candidatos

def gerar_post_recomendados(produtos, nicho):
    validos = [p for p in produtos if float(p.get("priceMin") or 0) > 0]
    if not validos:
        return None

    def score(p):
        vendas = float(p.get("sales") or 0)
        rating = float(p.get("ratingStar") or 0)
        return vendas * 0.7 + (rating * 1000) * 0.3

    # remove duplicados por nome antes de ranquear
    vistos = set()
    unicos = []
    for p in sorted(validos, key=score, reverse=True):
        nome = p.get("productName", "")
        if nome not in vistos:
            vistos.add(nome)
            unicos.append(p)
    top3 = unicos[:3]
    if not top3:
        return None

    emoji    = nicho["emoji"]
    canal    = nicho["canal"]
    hashtags = nicho["hashtags"]
    hora     = datetime.now().strftime("%H:%M")

    linhas = ""
    for p in top3:
        nome     = str(p.get("productName", ""))[:60]
        preco    = formatar_preco(p.get("priceMin", 0))
        vendas   = formatar_vendas(p.get("sales", 0))
        nota     = float(p.get("ratingStar", 0) or 0)
        estrelas = "⭐" * round(nota) if nota else ""
        link     = p.get("offerLink", "https://shopee.com.br")
        linhas  += f'\n{emoji} <a href="{link}"><b>{nome}</b></a>\n   💰 {preco} | {vendas} {estrelas}\n'

    return f"""🌟 <b>RECOMENDADOS DO DIA — {hora}</b> 🌟

Os mais vendidos e bem avaliados de hoje:
{linhas}
👆 Clica no produto pra conferir!

{hashtags}
📢 {canal}"""

def verificar_e_postar_recomendados():
    agora = datetime.now().hour
    if agora not in HORARIOS_RECOMENDADOS:
        return

    for nicho in NICHOS:
        canal = nicho["canal"]
        if ja_postou(ARQUIVO_CONTROLE_RECOMENDADOS, canal, agora):
            continue

        produtos = buscar_recomendados(nicho)
        texto    = gerar_post_recomendados(produtos, nicho)
        if not texto:
            continue

        if enviar_mensagem(texto, canal):
            print(f"[{datetime.now().strftime('%d/%m %H:%M')}] 🌟 Recomendados enviado para {canal}!")
            marcar_postado(ARQUIVO_CONTROLE_RECOMENDADOS, canal, agora)

        time.sleep(10)

def loop_extras():
    """Thread paralela: cuida de cupom geral + recomendados, checando a cada minuto."""
    while True:
        try:
            verificar_e_postar_cupons()
        except Exception as e:
            print(f"[Cupons] Erro no loop: {e}")
        try:
            verificar_e_postar_recomendados()
        except Exception as e:
            print(f"[Recomendados] Erro no loop: {e}")
        time.sleep(60)

# ============================================================
# INICIALIZAÇÃO
# ============================================================
if __name__ == "__main__":
    print("=" * 55)
    print("🤖 ACHADINHOBOT — 5 NICHOS + CUPOM + RECOMENDADOS")
    print(f"📅 {POSTS_POR_DIA} posts/dia por canal | {HORA_INICIO}h às {HORA_FIM}h")
    print(f"⏱️  1 post a cada {INTERVALO}s (~{INTERVALO//60} min)")
    print(f"🏷️  Cupom geral nos horários: {HORARIOS_CUPOM}h")
    print(f"🌟 Recomendados nos horários: {HORARIOS_RECOMENDADOS}h")
    print("📢 Canais:")
    for n in NICHOS:
        print(f"   {n['emoji']}  {n['canal']}")
    print("=" * 55)

    # Inicia cupom + recomendados em thread paralela
    Thread(target=loop_extras, daemon=True).start()
    print("🏷️  Módulo de cupom/recomendados ativo!")

    # Loop principal de produtos
    postar_todos()

    try:
        while True:
            time.sleep(INTERVALO)
            postar_todos()
    except KeyboardInterrupt:
        print("\nBot encerrado.")
