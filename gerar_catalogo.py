import base64
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
import os

# Descobre a pasta real onde este script está guardado para evitar erros de diretório no terminal
PASTA_DO_SCRIPT = Path(__file__).resolve().parent

# --- CONFIGURAÇÕES DO UTILIZADOR ---
ARQUIVO_LINKS_PADRAO = PASTA_DO_SCRIPT / "www.youtube.com_20260708_111546.txt"
ARQUIVO_SAIDA = PASTA_DO_SCRIPT / "catalogo.html"
ARQUIVO_CACHE_TITULOS = PASTA_DO_SCRIPT / "titulos_cache.json"

# Se este caminho for absoluto, é respeitado. Se for relativo, resolve na pasta do script.
CAMINHO_LOGO_INPUT = r"C:\Users\ribei\Downloads\channels4_profile.jpg"
ARQUIVO_LOGO = Path(CAMINHO_LOGO_INPUT) if Path(CAMINHO_LOGO_INPUT).is_absolute() else PASTA_DO_SCRIPT / CAMINHO_LOGO_INPUT

SEU_NUMERO_WHATSAPP = "5519996154687"
PASTA_PLAYLISTS = PASTA_DO_SCRIPT / "Playlists"
# -----------------------------------

class Cores:
    VERDE = '\033[92m'
    AZUL = '\033[94m'
    AMARELO = '\033[93m'
    VERMELHO = '\033[91m'
    RESET = '\033[0m'
    NEGRITO = '\033[1m'

def extrair_id_youtube(url):
    padroes = [
        r"youtube\.com/watch\?v=([^&\s]+)",
        r"youtu\.be/([^?\s]+)",
        r"youtube\.com/shorts/([^?\s]+)",
        r"youtube\.com/embed/([^?\s]+)",
    ]
    for padrao in padroes:
        resultado = re.search(padrao, url)
        if resultado:
            return resultado.group(1)
    return None

def carregar_cache():
    caminho = Path(ARQUIVO_CACHE_TITULOS)
    if not caminho.exists():
        return {}
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except Exception:
        return {}

def salvar_cache(cache):
    Path(ARQUIVO_CACHE_TITULOS).write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def buscar_titulo_youtube(video_id, cache):
    if video_id in cache:
        return cache[video_id]

    url_video = f"https://www.youtube.com/watch?v={video_id}"
    url_oembed = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(url_video)

    try:
        req = urllib.request.Request(
            url_oembed, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=5) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
            titulo = dados.get("title", "").strip()

            if not titulo:
                titulo = f"Video {video_id}"

            cache[video_id] = titulo
            salvar_cache(cache)
            return titulo
    except Exception:
        titulo = f"Video {video_id}"
        cache[video_id] = titulo
        salvar_cache(cache)
        return titulo

def carregar_logo_base64():
    caminho = Path(ARQUIVO_LOGO)
    if not caminho.exists():
        print(f"{Cores.AMARELO}[AVISO]{Cores.RESET} Logo não encontrada em: {ARQUIVO_LOGO}. O catálogo usará uma logo padrão.")
        return ""
    try:
        conteudo = caminho.read_bytes()
        logo = base64.b64encode(conteudo).decode("utf-8")
        return f"data:image/jpeg;base64,{logo}"
    except Exception as e:
        print(f"{Cores.VERMELHO}[ERRO]{Cores.RESET} Falha ao ler a logo: {e}")
        return ""

def processar_catalogo():
    print(f"{Cores.NEGRITO}{Cores.AZUL}========================================={Cores.RESET}")
    print(f"{Cores.NEGRITO}      CONSTRUTOR DE CATÁLOGO KRB   {Cores.RESET}")
    print(f"{Cores.NEGRITO}{Cores.AZUL}========================================={Cores.RESET}\n")

    cache = carregar_cache()
    videos = []
    vistos = set()
    playlists_disponiveis = set()
    global_id = 1

    caminho_playlists = Path(PASTA_PLAYLISTS)
    tem_playlists = False

    # 1. Verifica se existem playlists organizadas na pasta 'Playlists'
    if caminho_playlists.exists():
        ficheiros_playlists = [f for f in os.listdir(caminho_playlists) if f.endswith('.txt')]
        if ficheiros_playlists:
            tem_playlists = True
            print(f"{Cores.VERDE}[INFO]{Cores.RESET} Encontrada a pasta '{PASTA_PLAYLISTS}' com {len(ficheiros_playlists)} categorias!")
            
            for ficheiro in sorted(ficheiros_playlists):
                nome_categoria = os.path.splitext(ficheiro)[0]
                playlists_disponiveis.add(nome_categoria)
                caminho_completo = caminho_playlists / ficheiro
                
                print(f"\n -> A carregar categoria: {Cores.NEGRITO}{nome_categoria}{Cores.RESET}")
                
                try:
                    conteudo = caminho_completo.read_text(encoding="utf-8", errors="ignore")
                    urls = re.findall(
                        r"https?://(?:www\.)?(?:youtube\.com/watch\?v=[^\s\r\n]+|youtu\.be/[^\s\r\n]+|youtube\.com/shorts/[^\s\r\n]+|youtube\.com/embed/[^\s\r\n]+)",
                        conteudo
                    )
                    
                    contagem_categoria = 0
                    for url in urls:
                        video_id = extrair_id_youtube(url)
                        if not video_id or video_id in vistos:
                            continue
                        
                        vistos.add(video_id)
                        print(f"   Processando #{global_id:04d}: {video_id}...", end="\r")
                        titulo = buscar_titulo_youtube(video_id, cache)
                        
                        videos.append({
                            "ref": f"#{global_id:04d}",
                            "youtubeId": video_id,
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                            "titulo": titulo,
                            "playlist": nome_categoria
                        })
                        global_id += 1
                        contagem_categoria += 1
                    print(f"   Concluído! {contagem_categoria} vídeos adicionados.              ")
                except Exception as e:
                    print(f"\n{Cores.VERMELHO}[ERRO]{Cores.RESET} Falha ao carregar a playlist {ficheiro}: {e}")

    # 2. Caso não tenha pastas de playlist, usa o arquivo de texto geral padrão
    if not tem_playlists:
        print(f"{Cores.AMARELO}[AVISO]{Cores.RESET} Nenhuma playlist encontrada na pasta '{PASTA_PLAYLISTS}'.")
        print(f"A usar o arquivo padrão geral: {ARQUIVO_LINKS_PADRAO.name}")
        
        nome_categoria_padrao = "Geral"
        playlists_disponiveis.add(nome_categoria_padrao)
        caminho_padrao = Path(ARQUIVO_LINKS_PADRAO)
        
        if caminho_padrao.exists():
            try:
                conteudo = caminho_padrao.read_text(encoding="utf-8", errors="ignore")
                urls = re.findall(
                    r"https?://(?:www\.)?(?:youtube\.com/watch\?v=[^\s\r\n]+|youtu\.be/[^\s\r\n]+|youtube\.com/shorts/[^\s\r\n]+|youtube\.com/embed/[^\s\r\n]+)",
                    conteudo
                )
                
                print(f"\n -> A carregar ficheiro geral...")
                for url in urls:
                    video_id = extrair_id_youtube(url)
                    if not video_id or video_id in vistos:
                        continue
                    
                    vistos.add(video_id)
                    print(f"   Processando #{global_id:04d}: {video_id}...", end="\r")
                    titulo = buscar_titulo_youtube(video_id, cache)
                    
                    videos.append({
                        "ref": f"#{global_id:04d}",
                        "youtubeId": video_id,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "titulo": titulo,
                        "playlist": nome_categoria_padrao
                    })
                    global_id += 1
                print(f"   Concluído! {len(videos)} vídeos adicionados com sucesso.              ")
            except Exception as e:
                print(f"\n{Cores.VERMELHO}[ERRO]{Cores.RESET} Falha ao carregar o ficheiro padrão: {e}")
                return []
        else:
            print(f"\n{Cores.VERMELHO}[ERRO]{Cores.RESET} O ficheiro padrão '{ARQUIVO_LINKS_PADRAO.name}' não existe na pasta do script!")
            print(f"Caminho esperado: {ARQUIVO_LINKS_PADRAO}")
            print("\nPor favor, crie a pasta 'Playlists' com ficheiros .txt ou certifique-se de que o ficheiro geral está nessa pasta.")
            input("\nPressione Enter para sair...")
            return []

    return videos, sorted(list(playlists_disponiveis))

def gerar_html(videos, playlists):
    dados_json = json.dumps(videos, ensure_ascii=False)
    playlists_json = json.dumps(playlists, ensure_ascii=False)
    logo_base64 = carregar_logo_base64()

    html_template = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catálogo KRB | Compra Segura</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&display=swap" rel="stylesheet">

    <style>
        :root {
            --bg-base: #0f0f0f;
            --bg-surface: #212121;
            --bg-elevated: #3d3d3d;
            --text-primary: #f1f1f1;
            --text-secondary: #aaaaaa;
            --accent: #fff200;
            --accent-hover: #e6da00;
            --accent-text: #000000;
            --border-color: #3f3f3f;
            --whatsapp-green: #25D366;
            --mercado-livre: #FFE600;
            --mercado-livre-text: #2D3277;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Roboto', Arial, sans-serif;
            background-color: var(--bg-base);
            color: var(--text-primary);
            /* Espaço extra gigante no fundo para a barra não tapar os vídeos */
            padding-bottom: 240px; 
            overflow-x: hidden;
        }

        /* Layout Principal: Header de Topo */
        header {
            position: sticky;
            top: 0;
            z-index: 50;
            background-color: var(--bg-base);
            border-bottom: 1px solid var(--border-color);
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 16px;
            min-width: fit-content;
        }

        .logo {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid var(--accent);
        }

        .brand-text h1 {
            font-size: 20px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .brand-text p {
            font-size: 13px;
            color: var(--accent);
            margin-top: 2px;
            font-weight: 500;
        }

        /* Barra de Pesquisa Centralizada */
        .search-container {
            flex-grow: 1;
            max-width: 600px;
            display: flex;
            align-items: center;
            order: 2;
        }

        .search-box {
            display: flex;
            width: 100%;
            background-color: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 40px;
            overflow: hidden;
            transition: border-color 0.2s;
        }

        .search-box:focus-within {
            border-color: var(--text-secondary);
        }

        .search-input {
            flex-grow: 1;
            background: transparent;
            border: none;
            color: var(--text-primary);
            padding: 12px 16px;
            font-size: 16px;
            outline: none;
        }

        .search-input::placeholder {
            color: var(--text-secondary);
        }

        .search-btn {
            background-color: var(--bg-elevated);
            border: none;
            border-left: 1px solid var(--border-color);
            padding: 0 24px;
            color: var(--text-primary);
            cursor: pointer;
            transition: background-color 0.2s;
            font-size: 16px;
        }
        
        .search-btn:hover {
             background-color: #4d4d4d;
        }

        /* Layout de Conteúdo (Sidebar + Grelha) */
        .main-layout {
            display: flex;
            max-width: 1600px;
            margin: 0 auto;
        }

        /* Sidebar de Categorias */
        .sidebar {
            width: 240px;
            flex-shrink: 0;
            padding: 24px 16px;
            border-right: 1px solid var(--border-color);
            height: calc(100vh - 75px);
            position: sticky;
            top: 75px;
            overflow-y: auto;
        }

        .sidebar-title {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 12px;
            padding: 0 12px;
            color: var(--text-primary);
        }

        .category-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .category-item {
            padding: 10px 12px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 16px;
            transition: background-color 0.2s;
        }

        .category-item i {
            font-size: 18px;
            color: var(--text-secondary);
            width: 24px;
            text-align: center;
        }

        .category-item:hover {
            background-color: var(--bg-surface);
        }

        .category-item.active {
            background-color: var(--bg-surface);
            font-weight: 700;
            color: var(--accent);
        }

        .category-item.active i {
            color: var(--accent);
        }

        /* Área de Vídeos */
        .content-area {
            flex-grow: 1;
            padding: 24px;
            overflow-x: hidden;
        }

        .stats-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            flex-wrap: wrap;
            gap: 12px;
            background-color: var(--bg-surface);
            padding: 12px 20px;
            border-radius: 12px;
        }

        .stats-info {
            font-size: 15px;
            color: var(--text-secondary);
        }

        .stats-info span {
            color: var(--text-primary);
            font-weight: 700;
        }

        .video-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            row-gap: 32px;
        }

        /* Card de Vídeo Moderno */
        .video-card {
            display: flex;
            flex-direction: column;
            gap: 12px;
            cursor: pointer;
        }

        .thumbnail-wrapper {
            position: relative;
            width: 100%;
            border-radius: 12px;
            overflow: hidden;
            aspect-ratio: 16/9;
            background-color: var(--bg-surface);
        }

        .thumbnail {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }

        .video-card:hover .thumbnail {
            transform: scale(1.03);
        }

        .video-info {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .video-title-wrap {
            display: flex;
            gap: 12px;
            align-items: flex-start;
        }

        .ref-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background-color: var(--bg-surface);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 700;
            color: var(--accent);
            flex-shrink: 0;
            border: 1px solid var(--border-color);
        }

        .video-title {
            font-size: 16px;
            font-weight: 500;
            color: var(--text-primary);
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .video-category {
            font-size: 13px;
            color: var(--text-secondary);
            padding-left: 48px;
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 4px;
        }

        /* Botões de Ação no Card */
        .card-actions {
            display: flex;
            gap: 8px;
            padding-left: 48px;
            margin-top: 8px;
        }

        .btn-action {
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 700;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.2s;
            flex: 1;
        }

        .btn-watch {
            background-color: var(--bg-surface);
            color: var(--text-primary);
            flex: 0.5;
        }

        .btn-watch:hover {
            background-color: var(--bg-elevated);
        }

        .btn-select {
            background-color: #2a2a2a;
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }

        .btn-select.selected {
            background-color: var(--accent);
            color: var(--accent-text);
            border-color: var(--accent);
        }

        /* ========================================================
           BARRA GIGANTE DO CARRINHO (MERCADO LIVRE/WHATSAPP)
           ======================================================== */
        .giant-checkout-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #111111;
            border-top: 4px solid var(--mercado-livre);
            padding: 16px 20px 24px 20px;
            z-index: 999;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
            box-shadow: 0 -10px 40px rgba(0,0,0,0.9);
            transform: translateY(120%);
            transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        .giant-checkout-bar.show {
            transform: translateY(0);
        }

        .cart-title {
            font-size: 22px;
            font-weight: 700;
            color: #fff;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .cart-title i {
            color: var(--accent);
            font-size: 26px;
        }

        .cart-count-number {
            color: var(--accent);
            font-size: 32px;
            font-weight: 900;
            padding: 0 6px;
            display: inline-block;
        }

        .btn-giant-whatsapp {
            background-color: var(--whatsapp-green);
            color: #fff;
            border: none;
            width: 100%;
            max-width: 800px;
            padding: 16px 20px;
            border-radius: 16px;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 6px;
            box-shadow: 0 8px 25px rgba(37, 211, 102, 0.4);
            animation: pulse-green 2s infinite;
        }
        
        .btn-main-text {
            font-size: 22px;
            font-weight: 900;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .btn-sub-text {
            font-size: 13px;
            font-weight: 500;
            background: rgba(0,0,0,0.2);
            padding: 4px 14px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .btn-giant-whatsapp i.fa-whatsapp {
            font-size: 28px;
        }

        /* Animações Mágicas de Conversão */
        @keyframes pulse-green {
            0% { box-shadow: 0 0 0 0 rgba(37, 211, 102, 0.7); transform: scale(1); }
            50% { transform: scale(1.02); }
            70% { box-shadow: 0 0 0 15px rgba(37, 211, 102, 0); transform: scale(1); }
            100% { box-shadow: 0 0 0 0 rgba(37, 211, 102, 0); transform: scale(1); }
        }

        .pop-animation {
            animation: pop 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        @keyframes pop {
            0% { transform: scale(1); }
            50% { transform: scale(1.8); color: #fff; }
            100% { transform: scale(1); }
        }

        /* Modal do Player */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0,0,0,0.95);
            z-index: 2000;
            display: none;
            justify-content: center;
            align-items: center;
            padding: 10px;
        }

        .player-container {
            width: 100%;
            max-width: 1000px;
            background-color: #000;
            border-radius: 12px;
            overflow: hidden;
            position: relative;
        }

        .player-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            background: linear-gradient(to bottom, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0) 100%);
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            z-index: 10;
        }

        .btn-open-yt {
            background-color: #ff0000;
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
            border: 1px solid #ff0000;
        }

        .btn-close-modal {
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }

        .video-wrapper {
            position: relative;
            padding-bottom: 56.25%; /* 16:9 */
            height: 0;
            background: #111;
        }

        .video-wrapper iframe {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: 0;
            z-index: 5;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-secondary);
            grid-column: 1 / -1;
            display: none;
        }
        
        .empty-state i {
            font-size: 64px;
            margin-bottom: 16px;
            opacity: 0.5;
        }

        /* Responsividade Extrema para Mobile */
        @media (max-width: 768px) {
            header {
                flex-direction: column;
                align-items: stretch;
                padding: 16px;
                gap: 16px;
            }

            .header-brand {
                justify-content: space-between;
            }
            
            .brand-text p {
                display: block;
                font-size: 13px;
            }

            .main-layout {
                flex-direction: column;
            }

            /* Sidebar vira barra de arrastar no mobile */
            .sidebar {
                width: 100%;
                height: auto;
                padding: 12px 16px;
                border-right: none;
                border-bottom: 1px solid var(--border-color);
                position: relative;
                top: 0;
                display: flex;
                flex-direction: row;
                overflow-x: auto;
                gap: 12px;
            }
            
            .sidebar::-webkit-scrollbar {
                display: none;
            }

            .sidebar-title {
                display: none;
            }

            .category-list {
                flex-direction: row;
            }

            .category-item {
                background-color: var(--bg-surface);
                border-radius: 20px;
                padding: 10px 20px;
                white-space: nowrap;
                font-size: 15px;
            }

            .content-area {
                padding: 16px;
            }

            .video-grid {
                grid-template-columns: 1fr;
                gap: 24px;
            }
            
            .stats-header {
                flex-direction: column;
                align-items: flex-start;
            }

            .btn-giant-whatsapp {
                padding: 16px;
            }
            
            .btn-main-text {
                font-size: 18px;
            }

            .cart-title {
                font-size: 20px;
            }
        }
    </style>
</head>
<body>

    <header>
        <div class="header-brand">
            <img class="logo" id="logo-img" alt="Logo">
            <div class="brand-text">
                <h1>Catálogo de Amostras</h1>
                <p>Toque em "Adicionar" para pedir os vídeos</p>
            </div>
        </div>

        <div class="search-container">
            <div class="search-box">
                <input type="text" id="searchInput" class="search-input" placeholder="Pesquisar por título ou #ref..." autocomplete="off">
                <button class="search-btn" id="searchBtn"><i class="fa-solid fa-magnifying-glass"></i></button>
            </div>
        </div>
    </header>

    <div class="main-layout">
        <aside class="sidebar">
            <h2 class="sidebar-title">Navegar por</h2>
            <ul class="category-list" id="categoryList">
                <!-- Gerado por JS -->
            </ul>
        </aside>

        <main class="content-area">
            <div class="stats-header">
                <div class="stats-info">A mostrar <span id="countDisplay">0</span> opções de vídeo</div>
            </div>

            <div class="video-grid" id="videoGrid">
                <!-- Gerado por JS -->
            </div>
            
            <div class="empty-state" id="emptyState">
                <i class="fa-solid fa-video-slash"></i>
                <h3>Nenhum vídeo encontrado.</h3>
                <p>Tente procurar por outras palavras.</p>
            </div>
        </main>
    </div>

    <!-- ==========================================
         CARRINHO GIGANTE FIXO NO FUNDO 
         ========================================== -->
    <div class="giant-checkout-bar" id="giantCart">
        <div class="cart-title">
            <i class="fa-solid fa-cart-shopping"></i> Carrinho: 
            <span class="cart-count-number" id="giantCartCount">0</span> vídeos
        </div>
        <button class="btn-giant-whatsapp" onclick="sendOrder()">
            <div class="btn-main-text">
                <i class="fa-brands fa-whatsapp"></i> Comprar (Mercado Livre)
            </div>
            <div class="btn-sub-text">
                <i class="fa-solid fa-shield-halved"></i> O pedido será enviado via WhatsApp
            </div>
        </button>
    </div>

    <!-- Player Modal -->
    <div class="modal-overlay" id="playerModal" onclick="closePlayer()">
        <div class="player-container" onclick="event.stopPropagation()">
            <div class="player-header">
                <a id="btnOpenYoutube" href="#" target="_blank" class="btn-open-yt"><i class="fa-brands fa-youtube"></i> Abrir no YouTube</a>
                <button class="btn-close-modal" onclick="closePlayer()"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="video-wrapper">
                <iframe id="videoIframe" src="" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
            </div>
        </div>
    </div>

    <script>
        // Dados Injetados
        const videosData = DADOS_VIDEOS;
        const playlists = DADOS_PLAYLISTS;
        const zapNumber = "NUMERO_WHATSAPP";
        const logoB64 = "LOGO_BASE64_PLACEHOLDER";

        if(logoB64) {
            document.getElementById('logo-img').src = logoB64;
        } else {
            document.getElementById('logo-img').style.display = 'none';
        }

        // Estado da Aplicação
        let currentCategory = "Todos";
        let searchQuery = "";
        const selectedRefs = new Set();
        let displayLimit = 30; // Paginação inicial

        // Elementos DOM
        const categoryListEl = document.getElementById('categoryList');
        const videoGridEl = document.getElementById('videoGrid');
        const searchInput = document.getElementById('searchInput');
        const countDisplay = document.getElementById('countDisplay');
        const giantCart = document.getElementById('giantCart');
        const giantCartCount = document.getElementById('giantCartCount');
        const emptyState = document.getElementById('emptyState');

        // Função para remover acentos e facilitar a busca
        function normalizeString(str) {
            if (!str) return "";
            return str.toString().toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
        }

        // 1. Renderiza a Sidebar de Categorias
        function renderCategories() {
            categoryListEl.innerHTML = '';
            
            // Item "Todos"
            const liTodos = document.createElement('li');
            liTodos.className = `category-item ${currentCategory === 'Todos' ? 'active' : ''}`;
            liTodos.innerHTML = `<i class="fa-solid fa-border-all"></i> Tudo`;
            liTodos.onclick = () => {
                currentCategory = "Todos";
                renderCategories();
                filterAndRenderVideos();
            };
            categoryListEl.appendChild(liTodos);

            // Itens Dinâmicos
            playlists.forEach(pl => {
                const li = document.createElement('li');
                li.className = `category-item ${currentCategory === pl ? 'active' : ''}`;
                li.innerHTML = `<i class="fa-solid fa-list-ul"></i> ${pl}`;
                li.onclick = () => {
                    currentCategory = pl;
                    renderCategories();
                    filterAndRenderVideos();
                };
                categoryListEl.appendChild(li);
            });
        }

        // 2. Cria o Card de Vídeo
        function createVideoCard(video) {
            const isSelected = selectedRefs.has(video.ref);
            
            return `
                <div class="video-card">
                    <div class="thumbnail-wrapper" onclick="openPlayer('${video.youtubeId}', '${video.url}')">
                        <img class="thumbnail" loading="lazy" src="https://img.youtube.com/vi/${video.youtubeId}/mqdefault.jpg" alt="${video.titulo}">
                    </div>
                    <div class="video-info">
                        <div class="video-title-wrap">
                            <div class="ref-avatar">${video.ref.replace('#','')}</div>
                            <h3 class="video-title" title="${video.titulo}">${video.titulo}</h3>
                        </div>
                        <div class="video-category">
                            <i class="fa-regular fa-folder-open"></i> ${video.playlist}
                        </div>
                        <div class="card-actions">
                            <button class="btn-action btn-watch" onclick="openPlayer('${video.youtubeId}', '${video.url}')">
                                <i class="fa-solid fa-play"></i> Assistir
                            </button>
                            <!-- Botão MUITO claro de adicionar -->
                            <button class="btn-action btn-select ${isSelected ? 'selected' : ''}" onclick="toggleSelection('${video.ref}', this)">
                                <i class="fa-solid ${isSelected ? 'fa-check' : 'fa-cart-plus'}"></i> 
                                ${isSelected ? 'Adicionado' : '🛒 Adicionar'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        // 3. Filtra e Renderiza a Grelha de Vídeos
        function filterAndRenderVideos() {
            // Aplicar Filtros (Categoria E Busca combinados perfeitamente)
            const normalizedQuery = normalizeString(searchQuery);
            
            const filtered = videosData.filter(v => {
                const matchCategory = currentCategory === "Todos" || v.playlist === currentCategory;
                
                const searchTarget = normalizeString(`${v.titulo} ${v.ref} ${v.playlist}`);
                const matchSearch = !normalizedQuery || searchTarget.includes(normalizedQuery);
                
                return matchCategory && matchSearch;
            });

            // Atualizar UI
            countDisplay.textContent = filtered.length;
            
            if (filtered.length === 0) {
                videoGridEl.innerHTML = '';
                emptyState.style.display = 'block';
            } else {
                emptyState.style.display = 'none';
                
                // Paginação Simples para performance
                const toDisplay = filtered.slice(0, displayLimit);
                videoGridEl.innerHTML = toDisplay.map(createVideoCard).join('');
            }
        }

        // 4. Lidar com Pesquisa (Em tempo real)
        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value;
            displayLimit = 30; // Reseta limite ao pesquisar
            filterAndRenderVideos();
        });

        // 5. Lidar com Scroll infinito (Lazy loading de blocos)
        window.addEventListener('scroll', () => {
            if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
                displayLimit += 30;
                filterAndRenderVideos(); // Re-renderiza com mais itens
            }
        });

        // 6. Seleção e Carrinho (COM ANIMAÇÃO DE PULSAR)
        window.toggleSelection = function(ref, btnElement) {
            if (selectedRefs.has(ref)) {
                selectedRefs.delete(ref);
                btnElement.classList.remove('selected');
                btnElement.innerHTML = `<i class="fa-solid fa-cart-plus"></i> 🛒 Adicionar`;
            } else {
                selectedRefs.add(ref);
                btnElement.classList.add('selected');
                btnElement.innerHTML = `<i class="fa-solid fa-check"></i> Adicionado`;
            }
            updateCartUI();
        };

        function updateCartUI() {
            const count = selectedRefs.size;
            
            // Verifica se o número mudou para fazer a animação de "pular"
            if(giantCartCount.textContent != count) {
                giantCartCount.textContent = count;
                
                // Força o reinício da animação removendo e adicionando a classe
                giantCartCount.classList.remove('pop-animation');
                void giantCartCount.offsetWidth; // truque de programação para reiniciar a animação
                giantCartCount.classList.add('pop-animation');
            }
            
            // Mostra ou esconde a barra gigante
            if (count > 0) {
                giantCart.classList.add('show');
            } else {
                giantCart.classList.remove('show');
            }
        }

        // 7. Ações de Envio Direto para o WhatsApp (Mercado Livre)
        window.sendOrder = function() {
            if(selectedRefs.size === 0) return;
            
            const list = Array.from(selectedRefs).sort().map(ref => {
                const v = videosData.find(x => x.ref === ref);
                return `${v.ref} - ${v.titulo} (${v.playlist})`;
            }).join('\\n');
            
            const mensagem = `Olá! Quero fechar a compra dos seguintes vídeos:\n\n${list}\n\nPor favor, envie-me o link de pagamento do Mercado Livre para finalizarmos de forma segura!`;
            
            const text = encodeURIComponent(mensagem);
            window.open(`https://wa.me/${zapNumber}?text=${text}`, '_blank');
        };

        window.openPlayer = function(id, url) {
            const modal = document.getElementById('playerModal');
            const iframe = document.getElementById('videoIframe');
            const btnYt = document.getElementById('btnOpenYoutube');
            
            // Alterado para youtube-nocookie para tentar evitar alguns bloqueios locais (Erro 153)
            iframe.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0`;
            btnYt.href = url || `https://www.youtube.com/watch?v=${id}`;
            
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden'; // Impede scroll do site atrás do vídeo
        };

        window.closePlayer = function() {
            const modal = document.getElementById('playerModal');
            const iframe = document.getElementById('videoIframe');
            iframe.src = '';
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        };

        // Inicialização
        renderCategories();
        filterAndRenderVideos();

    </script>
</body>
</html>
""".replace("DADOS_VIDEOS", dados_json).replace("DADOS_PLAYLISTS", playlists_json).replace("NUMERO_WHATSAPP", SEU_NUMERO_WHATSAPP).replace("LOGO_BASE64_PLACEHOLDER", logo_base64)

    try:
        Path(ARQUIVO_SAIDA).write_text(html_template, encoding="utf-8")
        print(f"\n{Cores.VERDE}=== SUCESSO COGNITIVO! ==={Cores.RESET}")
        print(f"O seu catálogo unificado foi criado perfeitamente!")
        print(f"Ficheiro gerado: {Cores.NEGRITO}{ARQUIVO_SAIDA}{Cores.RESET}")
        print(f"Cache de títulos: {Cores.NEGRITO}{ARQUIVO_CACHE_TITULOS}{Cores.RESET}")
    except Exception as e:
        print(f"\n{Cores.VERMELHO}[ERRO]{Cores.RESET} Não foi possível gravar o arquivo HTML: {e}")

def main():
    resultado = processar_catalogo()
    if not resultado:
        return
        
    videos, playlists = resultado
    if not videos:
        print(f"\n{Cores.VERMELHO}[ERRO]{Cores.RESET} Nenhum link do YouTube válido foi processado.")
        return

    gerar_html(videos, playlists)

    print(f"\nTotal de vídeos unificados: {len(videos)}")
    print(f"Categorias detetadas: {len(playlists)}")
    print(f"\nDê dois cliques em '{ARQUIVO_SAIDA.name}' para testar o catálogo no navegador!")
    print(f"{Cores.NEGRITO}{Cores.AZUL}========================================={Cores.RESET}")
    input("\nPressione [ENTER] para fechar...")

if __name__ == "__main__":
    main()