import base64
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
import os

# --- CONFIGURAÇÕES DE CAMINHOS REAIS (FIXOS PARA EVITAR ERROS DO WINDOWS) ---
PASTA_DO_SCRIPT = Path(r"C:\Users\ribei\Downloads\catalogo")
PASTA_PLAYLISTS = Path(r"C:\Users\ribei\Downloads\catalogo\Playlists")
ARQUIVO_LINKS_PADRAO = PASTA_DO_SCRIPT / "www.youtube.com_20260708_111546.txt"
ARQUIVO_SAIDA = PASTA_DO_SCRIPT / "catalogo.html"
ARQUIVO_CACHE_TITULOS = PASTA_DO_SCRIPT / "titulos_cache.json"
CAMINHO_LOGO_INPUT = r"C:\Users\ribei\Downloads\channels4_profile.jpg"
ARQUIVO_LOGO = Path(CAMINHO_LOGO_INPUT)

# Número atualizado com DDD 19
SEU_NUMERO_WHATSAPP = "5519997985748"

# --- LISTA NEGRA DE MÚSICAS COM ERRO ---
NUMEROS_PARA_REMOVER = {
    69, 99, 355, 690, 733, 825, 1226, 1249, 1488, 1692, 1693, 
    1694, 1695, 1733, 1865, 3097, 3098, 3161, 3619, 3777, 3778, 
    3779, 3780, 3781, 3782, 3801, 3832, 4097, 4387, 4547, 4548, 
    4769, 5273, 5274
}
# -----------------------------------

class Cores:
    VERDE = '\033[92m'
    AZUL = '\033[94m'
    AMARELO = '\033[93m'
    VERMELHO = '\033[91m'
    RESET = '\033[0m'
    NEGRITO = '\033[1m'

def extrair_id_youtube(url):
    url = url.strip().replace("]", "").replace("[", "")
    padroes = [r"v=([^&\s]+)", r"youtu\.be/([^?\s]+)", r"shorts/([^?\s]+)", r"embed/([^?\s]+)"]
    for padrao in padroes:
        resultado = re.search(padrao, url)
        if resultado: return resultado.group(1)
    return None

def carregar_cache():
    caminho = Path(ARQUIVO_CACHE_TITULOS)
    if not caminho.exists(): return {}
    try: return json.loads(caminho.read_text(encoding="utf-8"))
    except: return {}

def salvar_cache(cache):
    Path(ARQUIVO_CACHE_TITULOS).write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

def buscar_titulo_youtube(video_id, cache):
    if video_id in cache: return cache[video_id]
    url_video = f"https://www.youtube.com/watch?v={video_id}"
    url_oembed = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(url_video)
    try:
        req = urllib.request.Request(url_oembed, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
            titulo = dados.get("title", "").strip() or f"Video {video_id}"
            cache[video_id] = titulo
            salvar_cache(cache)
            return titulo
    except:
        titulo = f"Video {video_id}"
        cache[video_id] = titulo
        salvar_cache(cache)
        return titulo

def carregar_logo_base64():
    caminho = Path(ARQUIVO_LOGO)
    if not caminho.exists(): return ""
    try: return f"data:image/jpeg;base64,{base64.b64encode(caminho.read_bytes()).decode('utf-8')}"
    except: return ""

def processar_catalogo():
    print(f"{Cores.NEGRITO}{Cores.AZUL}========================================={Cores.RESET}")
    print(f"{Cores.NEGRITO}    CONSTRUTOR DE CATÁLOGO KRB   {Cores.RESET}")
    print(f"{Cores.NEGRITO}{Cores.AZUL}========================================={Cores.RESET}\n")

    cache = carregar_cache()
    videos, vistos, playlists_disponiveis = [], set(), set()
    contador_leitura, global_id = 1, 1
    tem_playlists = False

    if PASTA_PLAYLISTS.exists():
        ficheiros_playlists = [f for f in os.listdir(PASTA_PLAYLISTS) if f.endswith('.txt')]
        if ficheiros_playlists:
            tem_playlists = True
            for ficheiro in sorted(ficheiros_playlists):
                nome_categoria = os.path.splitext(ficheiro)[0]
                playlists_disponiveis.add(nome_categoria)
                try:
                    conteudo = (PASTA_PLAYLISTS / ficheiro).read_text(encoding="utf-8", errors="ignore")
                    urls = re.findall(r"https?://[^\s\r\n]+", conteudo)
                    for url in urls:
                        video_id = extrair_id_youtube(url)
                        if not video_id or video_id in vistos: continue
                        vistos.add(video_id)
                        if contador_leitura in NUMEROS_PARA_REMOVER:
                            contador_leitura += 1
                            continue
                        titulo = buscar_titulo_youtube(video_id, cache)
                        videos.append({"ref": f"#{global_id:04d}", "youtubeId": video_id, "url": f"https://www.youtube.com/watch?v={video_id}", "titulo": titulo, "playlist": nome_categoria})
                        global_id += 1
                        contador_leitura += 1
                except Exception as e: print(f"Erro ao ler {ficheiro}: {e}")

    if not tem_playlists and ARQUIVO_LINKS_PADRAO.exists():
        nome_categoria = "Geral"
        playlists_disponiveis.add(nome_categoria)
        conteudo = ARQUIVO_LINKS_PADRAO.read_text(encoding="utf-8", errors="ignore")
        urls = re.findall(r"https?://[^\s\r\n]+", conteudo)
        for url in urls:
            video_id = extrair_id_youtube(url)
            if not video_id or video_id in vistos: continue
            vistos.add(video_id)
            if contador_leitura in NUMEROS_PARA_REMOVER:
                contador_leitura += 1
                continue
            titulo = buscar_titulo_youtube(video_id, cache)
            videos.append({"ref": f"#{global_id:04d}", "youtubeId": video_id, "url": f"https://www.youtube.com/watch?v={video_id}", "titulo": titulo, "playlist": nome_categoria})
            global_id += 1
            contador_leitura += 1

    return videos, sorted(list(playlists_disponiveis))

def gerar_html(videos, playlists):
    dados_json = json.dumps(videos, ensure_ascii=False)
    playlists_json = json.dumps(playlists, ensure_ascii=False)
    logo_base64 = carregar_logo_base64()

    html_template = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Catálogo KRB — Playbacks Premium</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-void:      #060606; --bg-base:      #0b0b0d; --bg-surface:   #131316; --bg-elevated:  #1c1c21;
            --bg-hover:     #24242b; --line:         #23232a; --line-strong:  #35353f; --text-hi:      #f5f5f7;
            --text-md:      #b8b8c2; --text-lo:      #7a7a86; --krb-yellow:   #FFD100; --krb-yellow-2: #FFE566;
            --wa:           #25D366; --wa-d:         #128C7E; --radius-md: 12px; --radius-lg: 16px;
            --shadow-card: 0 8px 24px -12px rgba(0,0,0,0.6);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        
        html { scroll-behavior: smooth; overflow-x: hidden; max-width: 100vw; }
        body { font-family: 'DM Sans', -apple-system, sans-serif; background: radial-gradient(1200px 600px at 15% -10%, rgba(255,209,0,0.06), transparent 60%), var(--bg-base); color: var(--text-hi); padding-bottom: 180px; overflow-x: hidden; width: 100%; max-width: 100vw; -webkit-font-smoothing: antialiased; }
        
        .app-header { position: sticky; top: 0; z-index: 60; backdrop-filter: saturate(140%) blur(18px); -webkit-backdrop-filter: saturate(140%) blur(18px); background: rgba(11,11,13,0.85); border-bottom: 1px solid var(--line); width: 100%; }
        .header-inner { max-width: 1600px; margin: 0 auto; padding: 12px 16px; display: flex; flex-direction: column; gap: 10px; }
        
        @media (min-width: 769px) { .header-inner { display: grid; grid-template-columns: auto 1fr auto; gap: 24px; padding: 14px 24px; } }

        .brand { display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 10px; }
        .brand-meta-left { display: flex; align-items: center; gap: 10px; }
        .brand-logo-wrap { width: 38px; height: 38px; border-radius: 10px; background: #1a1a1f; display: flex; align-items: center; justify-content: center; overflow: hidden; border: 1px solid var(--line-strong); }
        .brand-logo-wrap img { width: 100%; height: 100%; object-fit: cover; }
        .brand-logo-wrap .fallback { color: var(--krb-yellow); font-family: 'Sora'; font-weight: 800; font-size: 16px; }
        .brand-text h1 { font-family: 'Sora'; font-size: 16px; font-weight: 700; color: var(--text-hi); }
        .brand-text h1 span.k { color: var(--krb-yellow); }
        .brand-text .subtitle { font-size: 11px; color: var(--text-lo); margin-top: 1px; }
        
        .search-wrap { width: 100%; }
        .search-box { display: flex; align-items: center; gap: 8px; background: var(--bg-surface); border: 1px solid var(--line); border-radius: 999px; padding: 8px 14px; }
        .search-input { flex: 1; background: transparent; border: none; outline: none; color: var(--text-hi); font-size: 14px; font-weight: 500; min-width: 0; }
        .search-clear { display: none; background: transparent; border: none; cursor: pointer; color: var(--text-lo); }
        .kbd { display: none; }
        
        @media (min-width: 769px) {
            .search-wrap { max-width: 450px; justify-self: center; }
            .kbd { display: inline-flex; font-family: 'Sora'; font-size: 10px; padding: 4px 7px; border-radius: 6px; background: var(--bg-elevated); border: 1px solid var(--line-strong); color: var(--text-md); }
            .brand { width: auto; }
        }

        .header-actions { display: flex; gap: 8px; align-items: center; }
        .icon-btn { position: relative; width: 36px; height: 36px; display: inline-flex; align-items: center; justify-content: center; border-radius: 8px; background: var(--bg-surface); border: 1px solid var(--line); color: var(--text-md); cursor: pointer; }
        .icon-btn .badge { position: absolute; top: -4px; right: -4px; min-width: 18px; height: 18px; border-radius: 999px; background: var(--krb-yellow); color: #000; font-size: 10px; font-weight: 800; display: none; align-items: center; justify-content: center; }
        .icon-btn.has-items .badge { display: inline-flex; }
        
        .stats-strip { max-width: 1600px; margin: 0 auto; padding: 6px 16px 0; display: flex; flex-wrap: wrap; gap: 4px 12px; font-size: 12px; color: var(--text-md); }
        .stats-strip .stat b { color: var(--text-hi); }
        
        .layout { max-width: 1600px; margin: 0 auto; padding: 12px; display: grid; grid-template-columns: 1fr; gap: 14px; }
        @media (min-width: 769px) { .layout { grid-template-columns: 240px 1fr; padding: 20px 24px; gap: 24px; } }

        .sidebar { position: fixed; top: 0; left: 0; width: 260px; height: 100dvh; background: var(--bg-base); padding: 24px 14px; transform: translateX(-105%); transition: transform 0.25s ease; z-index: 200; box-shadow: 20px 0 40px rgba(0,0,0,0.8); }
        .sidebar.open { transform: translateX(0); }
        .sidebar-title { font-family: 'Sora'; font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-lo); padding: 0 12px 8px; }
        .cat-list { list-style: none; display: flex; flex-direction: column; gap: 2px; max-height: calc(100vh - 100px); overflow-y: auto; }
        .cat-item { display: flex; align-items: center; gap: 10px; padding: 10px; border-radius: 8px; font-size: 14px; font-weight: 500; color: var(--text-md); cursor: pointer; position: relative; }
        .cat-item.active { background: var(--bg-surface); color: var(--text-hi); }
        .cat-item.active::before { content: ""; position: absolute; left: 0; top: 8px; bottom: 8px; width: 3px; background: var(--krb-yellow); }
        .cat-icon { color: var(--text-lo); width: 18px; text-align: center; }
        .cat-item.active .cat-icon { color: var(--krb-yellow); }
        
        @media (min-width: 769px) { .sidebar { position: sticky; top: 96px; height: calc(100vh - 120px); transform: translateX(0); z-index: 10; box-shadow: none; padding: 0; background: transparent; } .cat-list { max-height: none; } }

        .drawer-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 150; display: none; }
        .drawer-backdrop.show { display: block; }

        .pack-promo-banner { background: linear-gradient(90deg, #ffd100, #ff9900); color: #000; padding: 10px; border-radius: 10px; margin-bottom: 12px; font-family: 'Sora'; font-weight: 700; font-size: 11px; text-align: center; line-height: 1.3; }
        @media (min-width: 769px) { .pack-promo-banner { font-size: 13px; padding: 12px; text-align: left; display: flex; justify-content: space-between; } }

        .hero { padding: 16px; border-radius: var(--radius-md); background: #131316; border: 1px solid var(--line); margin-bottom: 12px; text-align: center; overflow: hidden; }
        .hero-eyebrow { font-family: 'Sora'; font-size: 10px; font-weight: 700; text-transform: uppercase; color: var(--krb-yellow); padding: 4px 8px; border-radius: 999px; background: rgba(255,209,0,0.1); margin-bottom: 8px; display: inline-flex; }
        .hero-title { font-size: 18px; font-weight: 800; font-family: 'Sora'; color: var(--text-hi); word-break: break-word; }
        .hero-title .hi { color: var(--krb-yellow); }
        .hero-cta { margin-top: 12px; display: flex; justify-content: center; }
        @media (min-width: 769px) { .hero { padding: 24px; text-align: left; margin-bottom: 20px; } .hero-title { font-size: 32px; } .hero-cta { justify-content: flex-start; } }

        .toolbar { display: flex; flex-direction: column; gap: 10px; margin-bottom: 14px; }
        .toolbar-left h2 { font-size: 18px; font-weight: 700; font-family: 'Sora'; }
        .toolbar-left .count { font-size: 12px; color: var(--text-lo); }
        
        .toolbar-right { display: flex; flex-wrap: wrap; gap: 6px; width: 100%; }
        .chip { flex: 1; text-align: center; padding: 8px; border-radius: 6px; background: var(--bg-surface); color: var(--text-md); border: 1px solid var(--line); font-size: 12px; font-weight: 600; cursor: pointer; }
        .chip.active { background: var(--krb-yellow); color: #000; border-color: var(--krb-yellow); }
        .sort-select { flex: 1 1 100%; width: 100%; background: var(--bg-surface); color: var(--text-hi); border: 1px solid var(--line); padding: 8px; border-radius: 6px; cursor: pointer; font-size: 12px; margin-top: 2px; }
        
        @media (min-width: 769px) { .toolbar { flex-direction: row; align-items: center; justify-content: space-between; } .toolbar-right { width: auto; flex-wrap: nowrap; } .chip { flex: none; padding: 8px 12px; border-radius: 999px; } .sort-select { flex: none; width: auto; margin-top: 0; } }

        .video-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 4px; }
        @media (min-width: 600px) { .video-grid { grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; } }

        .card { display: flex; flex-direction: column; height: 100%; padding: 10px; border-radius: 12px; background: var(--bg-surface); border: 1px solid var(--line); box-shadow: var(--shadow-card); position: relative; }
        .thumb { position: relative; width: 100%; aspect-ratio: 16/9; border-radius: 8px; overflow: hidden; background: #000; cursor: pointer; }
        .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
        
        .badges { position: absolute; top: 6px; left: 6px; display: flex; gap: 4px; z-index: 2; }
        .badge-tag { font-family: 'Sora'; font-size: 9px; font-weight: 800; padding: 3px 6px; border-radius: 4px; background: rgba(0,0,0,0.75); color: var(--text-hi); }
        .badge-tag.new { background: var(--krb-yellow); color: #000; }
        
        .fav-btn { position: absolute; top: 6px; right: 6px; width: 28px; height: 28px; border-radius: 50%; background: rgba(0,0,0,0.6); color: var(--text-md); border: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; font-size: 12px; z-index: 3; }
        .fav-btn.active { color: #ff4d5e; }
        .play-fab { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: 36px; height: 36px; background: var(--krb-yellow); color: #000; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; opacity: 0.85; pointer-events: none; }
        
        .card-title { font-family: 'Sora'; font-weight: 600; font-size: 12px; line-height: 1.35; margin: 10px 0 6px 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 32px; color: var(--text-hi); text-align: left; word-break: break-word; }
        .card-meta { display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--text-lo); margin-top: auto; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.03); }
        .card-meta .code { color: var(--krb-yellow); font-weight: 700; }
        
        .card-actions { display: flex; gap: 4px; margin-top: 8px; width: 100%; }
        
        .btn-action { width: 100%; padding: 10px 4px; border-radius: 8px; font-family: 'Sora'; font-weight: 700; font-size: 12px; border: 1px solid var(--line-strong); background: var(--bg-elevated); color: var(--text-hi); cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 4px; transition: all 0.15s ease; }
        .btn-action.add.selected { background: var(--krb-yellow) !important; color: #000 !important; border-color: var(--krb-yellow) !important; }

        @media (min-width: 769px) {
            .card { padding: 12px; } .card-title { font-size: 14px; height: 38px; } .btn-action { padding: 12px; font-size: 13px; }
        }

        .empty { grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--text-md); display: none; }
        
        .cart-container { position: fixed; bottom: 0; left: 0; right: 0; z-index: 900; display: none; flex-direction: column; padding: 12px 14px calc(12px + env(safe-area-inset-bottom)); background: #131316; border-top: 1px solid var(--line-strong); box-shadow: 0 -10px 30px rgba(0,0,0,0.9); }
        .pack-counter-balloon { background: var(--bg-elevated); border: 1px solid var(--line); padding: 6px 10px; border-radius: 6px; font-size: 11px; font-family: 'Sora'; font-weight: 600; text-align: center; margin-bottom: 6px; width: 100%; }
        .pack-counter-balloon b { color: var(--krb-yellow); }
        
        .cart-fab { display: flex; width: 100%; align-items: center; justify-content: space-between; gap: 10px; }
        .cart-main-clickable { display: flex; align-items: center; gap: 8px; text-align: left; cursor: pointer; }
        .cart-fab .cart-ico { width: 34px; height: 34px; border-radius: 50%; background: var(--krb-yellow); color: #000; display: flex; align-items: center; justify-content: center; font-size: 14px; }
        .cart-fab .cart-txt .top { font-family: 'Sora'; font-weight: 700; font-size: 12px; color: var(--text-hi); }
        .cart-fab .cart-txt .bot { font-size: 10px; color: var(--text-lo); }
        .cart-fab .go-btn { background: var(--wa); color: #fff; padding: 8px 12px; border-radius: 30px; font-family: 'Sora'; font-weight: 700; font-size: 12px; border: none; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; }

        @media (min-width: 769px) { .cart-container { bottom: 24px; right: 24px; left: auto; width: 320px; border-radius: 12px; border: 1px solid var(--line-strong); padding: 12px; background: var(--bg-elevated); } }

        .toast { position: fixed; top: 14px; left: 50%; transform: translateX(-50%) translateY(-20px); background: var(--bg-elevated); color: var(--text-hi); padding: 8px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; border: 1px solid var(--line-strong); opacity: 0; transition: all 0.2s ease; z-index: 3000; }
        .toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
        .toast i { color: var(--krb-yellow); margin-right: 4px; }
        
        .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.92); backdrop-filter: blur(8px); z-index: 2000; display: none; justify-content: center; align-items: center; padding: 10px; }
        .player-shell { width: 100%; max-width: 840px; background: #000; border-radius: 10px; overflow: hidden; position: relative; border: 1px solid var(--line-strong); }
        .player-header { position: absolute; top: 0; left: 0; right: 0; display: flex; justify-content: space-between; padding: 8px; z-index: 10; }
        .btn-close-modal { width: 30px; height: 30px; border-radius: 50%; background: rgba(255,255,255,0.2); border: none; color: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .video-wrapper { position: relative; padding-bottom: 56.25%; height: 0; background: #000; }
        .video-wrapper iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }
    </style>
</head>
<body>
    <header class="app-header">
        <div class="header-inner">
            <div class="brand">
                <div class="brand-meta-left">
                    <button class="icon-btn mobile-menu-btn" id="mobileMenuBtn" aria-label="Menu"><i class="fa-solid fa-bars"></i></button>
                    <div class="brand-logo-wrap"><img id="logo-img" alt="KRB Logo"><span class="fallback" id="logo-fallback" style="display:none;">K</span></div>
                    <div class="brand-text"><h1><span class="k">KRB</span> Catálogo<span class="tag">Oficial</span></h1><div class="subtitle">Playbacks Premium</div></div>
                </div>
                <div class="header-actions">
                    <button class="icon-btn" id="favToggleBtn" aria-label="Favoritos"><i class="fa-regular fa-heart"></i><span class="badge" id="favBadge">0</span></button>
                    <button class="icon-btn" id="cartToggleBtn" aria-label="Carrinho"><i class="fa-solid fa-cart-shopping"></i><span class="badge" id="cartBadge">0</span></button>
                </div>
            </div>
            <div class="search-wrap">
                <div class="search-box">
                    <i class="fa-solid fa-magnifying-glass"></i>
                    <input type="text" id="searchInput" class="search-input" placeholder="Pesquisar música ou código...">
                    <button class="search-clear" id="searchClear"><i class="fa-solid fa-xmark"></i></button>
                    <span class="kbd">Ctrl K</span>
                </div>
            </div>
        </div>
        <div class="stats-strip">
            <span class="stat"><b id="statVideos">0</b> playbacks</span>
            <span class="stat"><b id="statCategories">0</b> pastas</span>
        </div>
    </header>

    <div class="drawer-backdrop" id="drawerBackdrop"></div>
    <div class="layout">
        <aside class="sidebar" id="sidebar"><div class="sidebar-title">Categorias</div><ul class="cat-list" id="categoryList"></ul></aside>
        <main class="content">
            <div class="pack-promo-banner">
                <span><i class="fa-solid fa-music"></i> Catálogo de Playbacks</span>
                <span>R$ 10,00 por Playback</span>
            </div>
            <section class="hero">
                <span class="hero-eyebrow"><i class="fa-solid fa-crown"></i> KRB Playbacks</span>
                <h2 class="hero-title">Mais de <span class="hi" id="heroCount">0</span> arquivos de alta qualidade.</h2>
                <div class="hero-cta"><button class="btn btn-primary" id="ctaExplore"><i class="fa-solid fa-compact-disc"></i> Começar a Explorar</button></div>
            </section>
            <div class="toolbar">
                <div class="toolbar-left"><h2 id="sectionTitle">Todos os vídeos</h2><span class="count">— <b id="countDisplay">0</b> cadastrados</span></div>
                <div class="toolbar-right">
                    <button class="chip" id="chipFav"><i class="fa-solid fa-heart"></i> Favoritos</button>
                    <button class="chip" id="chipNew"><i class="fa-solid fa-fire"></i> Novidades</button>
                    <select class="sort-select" id="sortSelect">
                        <option value="recent">Mais recentes</option>
                        <option value="oldest">Mais antigos</option>
                        <option value="az">Ordem A → Z</option>
                    </select>
                </div>
            </div>
            <div class="video-grid" id="videoGrid"></div>
            <div class="empty" id="emptyState"><i class="fa-solid fa-video-slash"></i><h3>Nenhuma música encontrada</h3></div>
        </main>
    </div>

    <div class="cart-container" id="cartContainer">
        <div class="pack-counter-balloon" id="packBalloon">
            <span id="packBalloonText">Selecione músicas</span>
        </div>
        <div class="cart-fab">
            <div class="cart-main-clickable" onclick="sendOrder()">
                <div class="cart-ico"><i class="fa-solid fa-basket-shopping"></i></div>
                <div class="cart-txt"><span class="top"><span id="cartFabCount">0</span> selecionadas</span><span class="bot">Clique para finalizar</span></div>
            </div>
            <button class="go-btn" onclick="sendOrder()">Pedir via WhatsApp <i class="fa-brands fa-whatsapp"></i></button>
        </div>
    </div>

    <div class="toast" id="toast"><i class="fa-solid fa-circle-check"></i><span id="toastMsg">Adicionado!</span></div>

    <div class="modal-overlay" id="playerModal" onclick="closePlayer()">
        <div class="player-shell" onclick="event.stopPropagation()">
            <div class="player-header"><div></div><button class="btn-close-modal" onclick="closePlayer()"><i class="fa-solid fa-xmark"></i></button></div>
            <div class="video-wrapper"><iframe id="videoIframe" src="" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe></div>
        </div>
    </div>

    <script>
        const videosData = __DADOS_VIDEOS__; const playlists  = __DADOS_PLAYLISTS__;
        const zapNumber  = "__NUMERO_WHATSAPP__"; const logoB64    = "__LOGO_BASE64_PLACEHOLDER__";

        (function setupLogo() {
            const img = document.getElementById('logo-img'); const fb  = document.getElementById('logo-fallback');
            if (logoB64 && logoB64.length > 50) { img.src = logoB64; img.onerror = () => { img.style.display = 'none'; fb.style.display = 'block'; }; }
            else { img.style.display = 'none'; fb.style.display = 'block'; }
        })();

        let currentCategory = "Todos", searchQuery = "", sortMode = "recent", displayLimit = 40;
        const selectedRefs = new Set();
        
        function loadLocalSafely(key) { try { return JSON.parse(localStorage.getItem(key) || "[]"); } catch (e) { return []; } }
        function saveLocalSafely(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {} }
        const favRefs = new Set(loadLocalSafely('krb_favs'));
        
        const NEW_THRESHOLD = Math.max(1, Math.floor(videosData.length * 0.05));
        function refIndex(ref) { return parseInt(String(ref).replace(/[^0-9]/g, ''), 10) || 0; }
        function isNew(v) { return refIndex(v.ref) <= NEW_THRESHOLD; }
        
        function escapeHtml(s) { return String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }
        function normalizeString(str) { return (str||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""); }

        document.getElementById('statVideos').textContent = videosData.length;
        document.getElementById('statCategories').textContent = playlists.length;
        document.getElementById('heroCount').textContent = videosData.length;

        function renderCategories() {
            const list = document.getElementById('categoryList');
            let items = [{ id: "Todos", label: "Todos os vídeos", icon: "fa-solid fa-border-all" }, { id: "__FAV__", label: "Meus Favoritos", icon: "fa-solid fa-heart" }, { id: "__NEW__", label: "Novidades", icon: "fa-solid fa-fire" }];
            playlists.forEach(pl => items.push({ id: pl, label: pl, icon: "fa-solid fa-compact-disc" }));
            list.innerHTML = items.map(it => `<li class="cat-item ${currentCategory === it.id ? 'active' : ''}" onclick="selectCategory('${escapeHtml(it.id)}')"><i class="cat-icon ${it.icon}"></i><span style="flex:1">${escapeHtml(it.label)}</span></li>`).join('');
        }

        function selectCategory(cat) { currentCategory = cat; displayLimit = 40; renderCategories(); filterAndRender(); document.getElementById('sidebar').classList.remove('open'); document.getElementById('drawerBackdrop').classList.remove('show'); document.getElementById('sectionTitle').textContent = (cat === '__FAV__' ? 'Meus Favoritos' : (cat === '__NEW__' ? 'Novidades' : cat)); }

        function getFilteredList() {
            const q = normalizeString(searchQuery);
            let list = videosData.filter(v => {
                let matchCat = (currentCategory === "__FAV__") ? favRefs.has(v.ref) : (currentCategory === "__NEW__") ? isNew(v) : (currentCategory === "Todos" || v.playlist === currentCategory);
                return matchCat && (!q || normalizeString(v.titulo + " " + v.ref).includes(q));
            });
            
            if (sortMode === "recent") list.sort((a, b) => refIndex(a.ref) - refIndex(b.ref));
            else if (sortMode === "oldest") list.sort((a, b) => refIndex(b.ref) - refIndex(a.ref));
            else if (sortMode === "az") list.sort((a, b) => a.titulo.localeCompare(b.titulo));
            return list;
        }

        function filterAndRender(appendMode = false) {
            const list = getFilteredList();
            document.getElementById('countDisplay').textContent = list.length;
            const grid = document.getElementById('videoGrid'); const empty = document.getElementById('emptyState');
            if (list.length === 0) { grid.innerHTML = ''; empty.style.display = 'block'; return; } empty.style.display = 'none';
            
            const startIdx = appendMode ? grid.children.length : 0;
            const toDisplay = list.slice(startIdx, displayLimit);
            
            const cardsHtml = toDisplay.map(v => {
                const fav = favRefs.has(v.ref), sel = selectedRefs.has(v.ref);
                return `<div class="card" data-cardref="${escapeHtml(v.ref)}"><div class="thumb" onclick="openPlayer('${escapeHtml(v.youtubeId)}')"><div class="badges">${isNew(v) ? '<span class="badge-tag new">Novo</span>' : ''}<span class="badge-tag">${escapeHtml(v.ref)}</span></div><button class="fav-btn ${fav ? 'active' : ''}" onclick="event.stopPropagation(); toggleFav('${escapeHtml(v.ref)}', this)"><i class="${fav ? 'fa-solid' : 'fa-regular'} fa-heart"></i></button><img loading="lazy" src="https://i.ytimg.com/vi/${escapeHtml(v.youtubeId)}/mqdefault.jpg" onerror="this.src='https://i.ytimg.com/vi/${escapeHtml(v.youtubeId)}/0.jpg'"><div class="play-fab"><i class="fa-solid fa-play"></i></div></div><h3 class="card-title">${escapeHtml(v.titulo)}</h3><div class="card-meta"><span class="code">${escapeHtml(v.ref)}</span></div><div class="card-actions"><button class="btn-action add ${sel ? 'selected' : ''}" onclick="toggleSelection('${escapeHtml(v.ref)}', this)"><i class="fa-solid ${sel ? 'fa-check' : 'fa-cart-plus'}"></i> <span>${sel ? 'Adicionado' : 'Adicionar'}</span></button></div></div>`;
            }).join('');

            if (appendMode) { grid.insertAdjacentHTML('beforeend', cardsHtml); } 
            else { grid.innerHTML = cardsHtml; }
        }

        window.addEventListener('scroll', () => {
            if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 400) {
                const listCount = getFilteredList().length;
                const currentCardsCount = document.getElementById('videoGrid').children.length;
                if (currentCardsCount < listCount) {
                    displayLimit += 40;
                    filterAndRender(true);
                }
            }
        });

        window.toggleSelection = (ref, btn) => { 
            const cards = document.querySelectorAll(`[data-cardref="${ref}"] .btn-action.add`);
            if (selectedRefs.has(ref)) {
                selectedRefs.delete(ref);
                showToast('Removido do pedido'); 
            } else {
                selectedRefs.add(ref);
                showToast('Adicionado ao pedido'); 
            }
            
            cards.forEach(c => {
                if (selectedRefs.has(ref)) {
                    c.classList.add('selected');
                    c.querySelector('i').className = 'fa-solid fa-check';
                    c.querySelector('span').textContent = 'Adicionado';
                } else {
                    c.classList.remove('selected');
                    c.querySelector('i').className = 'fa-solid fa-cart-plus';
                    c.querySelector('span').textContent = 'Adicionar';
                }
            });
            updateCart();
        };
        
        window.toggleFav = (ref, btn) => { 
            favRefs.has(ref) ? favRefs.delete(ref) : favRefs.add(ref); 
            saveLocalSafely('krb_favs', Array.from(favRefs)); 
            showToast(favRefs.has(ref) ? 'Adicionado aos Favoritos' : 'Removido'); 
            document.getElementById('favBadge').textContent = favRefs.size; 
            if (currentCategory === "__FAV__") filterAndRender();
            else {
                const icon = btn.querySelector('i');
                if (favRefs.has(ref)) { btn.classList.add('active'); icon.className = 'fa-solid fa-heart'; }
                else { btn.classList.remove('active'); icon.className = 'fa-regular fa-heart'; }
            }
        };
        
        function updateCart() { 
            const count = selectedRefs.size; 
            document.getElementById('cartFabCount').textContent = count; 
            document.getElementById('cartBadge').textContent = count; 
            
            const container = document.getElementById('cartContainer');
            const balloon = document.getElementById('packBalloon');
            const txt = document.getElementById('packBalloonText');

            if (count > 0) {
                container.style.display = 'flex';
                balloon.style.display = 'block';
                
                // CÁLCULO DIRETO: R$ 10,00 por música
                const precoTotal = count * 10;
                txt.innerHTML = `🛒 Total: <b>R$ ${precoTotal.toFixed(2)}</b> (${count} música${count > 1 ? 's' : ''})`;
            } else {
                container.style.display = 'none';
                balloon.style.display = 'none';
            }
        }

        window.sendOrder = () => { 
            if (selectedRefs.size === 0) return; 
            const count = selectedRefs.size;
            let precoTotal = count * 10; // VALOR DIRETO NA MENSAGEM DO WHATSAPP

            const list = Array.from(selectedRefs).map(ref => { 
                const v = videosData.find(x => x.ref === ref); 
                return v ? `${v.ref} - ${v.titulo}` : ref; 
            }).join('\n'); 

            let resumoPreco = `Total de Músicas: ${count}\n`;
            resumoPreco += `💰 Valor Total: R$ ${precoTotal.toFixed(2)}`;

            window.open(`https://wa.me/${zapNumber}?text=${encodeURIComponent('Olá! Quero fechar o meu pedido com os seguintes playbacks:\n\n' + list + '\n\n' + resumoPreco)}`, '_blank'); 
        };

        window.openPlayer = (id) => { document.getElementById('videoIframe').src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1`; document.getElementById('playerModal').style.display = 'flex'; };
        window.closePlayer = () => { document.getElementById('videoIframe').src = ''; document.getElementById('playerModal').style.display = 'none'; };
        
        function showToast(msg) { 
            const t = document.getElementById('toast'); 
            document.getElementById('toastMsg').textContent = msg; 
            t.classList.add('show'); 
            setTimeout(() => t.classList.remove('show'), 1500); 
        }

        document.getElementById('searchInput').addEventListener('input', e => { searchQuery = e.target.value; displayLimit = 40; filterAndRender(); });
        document.getElementById('sortSelect').addEventListener('change', e => { sortMode = e.target.value; displayLimit = 40; filterAndRender(); });
        
        document.getElementById('mobileMenuBtn').addEventListener('click', () => { document.getElementById('sidebar').classList.add('open'); document.getElementById('drawerBackdrop').classList.add('show'); });
        document.getElementById('drawerBackdrop').addEventListener('click', () => { document.getElementById('sidebar').classList.remove('open'); document.getElementById('drawerBackdrop').classList.remove('show'); });
        document.getElementById('cartToggleBtn').addEventListener('click', () => { if(selectedRefs.size > 0) sendOrder(); else showToast('Nenhuma música selecionada'); });
        document.getElementById('favToggleBtn').addEventListener('click', () => selectCategory('__FAV__'));
        document.getElementById('chipFav').addEventListener('click', () => selectCategory(currentCategory === '__FAV__' ? 'Todos' : '__FAV__'));
        document.getElementById('chipNew').addEventListener('click', () => selectCategory(currentCategory === '__NEW__' ? 'Todos' : '__NEW__'));
        document.getElementById('ctaExplore').addEventListener('click', () => { document.getElementById('videoGrid').scrollIntoView({ behavior: 'smooth' }); });

        renderCategories(); filterAndRender(); document.getElementById('favBadge').textContent = favRefs.size;
    </script>
</body>
</html>
"""
    html_template = (
        html_template
        .replace("__DADOS_VIDEOS__", dados_json)
        .replace("__DADOS_PLAYLISTS__", playlists_json)
        .replace("__NUMERO_WHATSAPP__", SEU_NUMERO_WHATSAPP)
        .replace("__LOGO_BASE64_PLACEHOLDER__", logo_base64)
    )

    try:
        Path(ARQUIVO_SAIDA).write_text(html_template, encoding="utf-8")
        print(f"\n{Cores.VERDE}=== SUCESSO! ==={Cores.RESET}")
        print(f"O seu catálogo com o layout mobile milimetricamente ajustado foi gerado!")
        print(f"Ficheiro gerado: {Cores.NEGRITO}{ARQUIVO_SAIDA}{Cores.RESET}")
    except Exception as e:
        print(f"\n{Cores.VERMELHO}[ERRO]{Cores.RESET} Não foi possível gravar o arquivo HTML: {e}")

def main():
    resultado = processar_catalogo()
    if not resultado: return
    videos, playlists = resultado
    if not videos: return
    gerar_html(videos, playlists)
    print(f"\nTotal de vídeos unificados (limpos): {len(videos)}")
    input("\nPressione [ENTER] para fechar...")

if __name__ == "__main__":
    main()