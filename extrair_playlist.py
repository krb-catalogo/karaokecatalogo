import subprocess
import sys
import os
import re

def install_or_update_package(package):
    """Instala ou atualiza um pacote pip mostrando o progresso no terminal."""
    print(f"\n[INFO] A verificar/atualizar o {package}... Isto pode demorar alguns segundos.")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])

# Garante que as bibliotecas necessárias estão instaladas e atualizadas
try:
    import yt_dlp
except ImportError:
    try:
        install_or_update_package("yt-dlp")
        import yt_dlp
        print("[SUCESSO] Biblioteca instalada com sucesso!\n")
    except Exception as e:
        print(f"\n[ERRO] Não foi possível instalar automaticamente: {e}")
        print("Por favor, execute este comando no terminal manualmente: pip install -U yt-dlp")
        input("\nPressione Enter para fechar...")
        sys.exit(1)

def limpar_e_converter_url(url):
    """Limpa a URL e converte para o formato ideal de extração."""
    url = url.strip().replace('"', '').replace("'", "")
    
    match = re.search(r'(?:list=|\/playlist\/)([^&?/\s]+)', url)
    if match:
        playlist_id = match.group(1)
        
        # Se for Mix Automático (RD, UL, TL, PU, LL), mantém a URL de vídeo com o parâmetro da lista
        if playlist_id.startswith(("RD", "UL", "TL", "PU", "LL")):
            print(f"\n[INFO] Detetado Mix/Rádio do YouTube (ID: {playlist_id}). Extraindo lista do Mix...")
            return url, playlist_id

        # Se for uma playlist normal (PL...), converte para URL de playlist pura
        url_pura = f"https://www.youtube.com/playlist?list={playlist_id}"
        return url_pura, playlist_id
        
    return url, None

def extrair_links_playlist(url_original, nome_arquivo_saida):
    url_playlist, playlist_id = limpar_e_converter_url(url_original)
    
    ydl_opts = {
        'extract_flat': True,     # Apenas lê metadados (rápido e leve)
        'skip_download': True,
        'quiet': True,            # Silencia logs redundantes
        'no_warnings': True,      # Oculta avisos de terminal
        'ignoreerrors': True,     # Ignora vídeos privados/removidos sem parar a extração
        'noplaylist': False,      # FORÇA a extração de todos os itens da lista
    }
    
    print(f"\n[1/3] A analisar a ligação...")
    print(f" -> Endereço: {url_playlist}")
    print("\n[2/3] A estabelecer ligação ao YouTube... Por favor, aguarde.")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_playlist, download=False)
            
            if info:
                videos = []
                
                # Se for uma playlist/mix com múltiplos vídeos
                if 'entries' in info and info['entries'] is not None:
                    for item in info['entries']:
                        if item:
                            videos.append(item)
                # Se for realmente apenas 1 vídeo individual sem lista
                else:
                    videos = [info]
                
                total = len(videos)
                
                if total == 0:
                    print("\n[AVISO] A ligação foi estabelecida, mas nenhum vídeo foi encontrado nesta lista.")
                    return False
                
                print(f"\n[SUCESSO] Foram encontrados {total} vídeo(s)!")
                print(f"[3/3] A guardar os links no ficheiro '{nome_arquivo_saida}'...")
                
                with open(nome_arquivo_saida, 'w', encoding='utf-8') as f:
                    for idx, video in enumerate(videos, 1):
                        video_id = video.get('id')
                        if video_id:  # Garante que o ID do vídeo é válido
                            link_completo = f"https://www.youtube.com/watch?v={video_id}"
                            f.write(f"{link_completo}\n")
                        if idx % 50 == 0 or idx == total:
                            print(f" -> Processados {idx}/{total} links...")
                
                print(f"\n=== CONCLUÍDO COM SUCESSO! ===")
                print(f"Ficheiro guardado com sucesso em:")
                print(f" > {nome_arquivo_saida}")
                return True
            else:
                print("\n[AVISO] Não foi possível ler a playlist. Verifique se o link está correto.")
                return False
                
    except Exception as e:
        print(f"\n[ERRO] Ocorreu uma falha na extração: {e}")
        return False

if __name__ == "__main__":
    PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
    PASTA_PLAYLISTS = os.path.join(PASTA_DO_SCRIPT, "Playlists")

    if not os.path.exists(PASTA_PLAYLISTS):
        try:
            os.makedirs(PASTA_PLAYLISTS)
            print(f"[INFO] Pasta 'Playlists' criada com sucesso em:\n -> {PASTA_PLAYLISTS}\n")
        except Exception as e:
            print(f"[AVISO] Não foi possível criar a pasta 'Playlists' automaticamente: {e}")

    while True:
        print("\n=========================================")
        print("      EXTRATOR DE PLAYLISTS DO YOUTUBE   ")
        print("=========================================")
        
        url = input("\nCole aqui o link da sua playlist do YouTube e pressione Enter:\n> ").strip()
        
        if not url:
            print("\n[Aviso] Nenhum link foi introduzido.")
        else:
            nome_categoria = input("\nQual o nome desta categoria? (ex: Casamentos, Eletronica, Musicas):\n> ").strip()
            
            nome_categoria_limpo = re.sub(r'[\\/*?:"<>|]', "", nome_categoria)
            if not nome_categoria_limpo:
                nome_categoria_limpo = "categoria_sem_nome"
            
            nome_arquivo_saida = os.path.join(PASTA_PLAYLISTS, f"{nome_categoria_limpo}.txt")
                
            extrair_links_playlist(url, nome_arquivo_saida)
            
        opcao = input("\nQuer extrair outra playlist? Escreva S para Sim, ou pressione apenas ENTER para sair:\n> ").strip().upper()
        if opcao != 'S':
            print("\n=========================================")
            print("Extrator finalizado! Agora execute o seu 'gerar_catalogo.py' para atualizar o site.")
            input("Pressione a tecla [ENTER] para fechar esta janela...")
            break