import subprocess
import sys
import os
import re

def install_package(package):
    """Instala um pacote pip mostrando o progresso no terminal."""
    print(f"\n[INFO] A instalar o {package} no seu sistema... Isto pode demorar até 1 minuto.")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Garante que as bibliotecas necessárias estão instaladas
try:
    import yt_dlp
except ImportError:
    try:
        install_package("yt-dlp")
        import yt_dlp
        print("[SUCESSO] Biblioteca instalada com sucesso!\n")
    except Exception as e:
        print(f"\n[ERRO] Não foi possível instalar automaticamente: {e}")
        print("Por favor, execute este comando no terminal manualmente: pip install yt-dlp")
        input("\nPressione Enter para fechar...")
        sys.exit(1)

def limpar_e_converter_url(url):
    """Limpa a URL e converte links de 'watch?v=...&list=ID' para links de playlist puros."""
    url = url.strip().replace('"', '').replace("'", "")
    
    # Procura o ID da playlist usando Expressão Regular
    match = re.search(r'(?:list=|\/playlist\/)([^&?/\s]+)', url)
    if match:
        playlist_id = match.group(1)
        
        # Alerta se o ID da playlist parecer truncado (incompleto)
        if playlist_id.startswith("PL") and len(playlist_id) < 18:
            print(f"\n[AVISO CRÍTICO] O ID da sua playlist ({playlist_id}) parece estar INCOMPLETO!")
            print(f"Ele tem apenas {len(playlist_id)} caracteres. Geralmente, as playlists do YouTube têm entre 18 e 34 caracteres.")
            print("Verifique se copiou o link inteiro até ao fim de onde o obteve.")
        
        # Reconstrói para uma URL de playlist pura (muito mais estável para extração flat)
        url_pura = f"https://www.youtube.com/playlist?list={playlist_id}"
        return url_pura, playlist_id
        
    return url, None

def extrair_links_playlist(url_original, nome_arquivo_saida):
    url_playlist, playlist_id = limpar_e_converter_url(url_original)
    
    ydl_opts = {
        'extract_flat': True,  # Apenas lê metadados (rápido e leve)
        'skip_download': True,
        'quiet': True,         # Silencia logs redundantes para manter o terminal limpo
    }
    
    print(f"\n[1/3] A analisar o ID da playlist: {playlist_id if playlist_id else 'Não detetado'}")
    print(f" -> Endereço de ligação: {url_playlist}")
    print("\n[2/3] A estabelecer ligação ao YouTube... Por favor, aguarde.")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_playlist, download=False)
            
            if 'entries' in info:
                videos = info['entries']
                total = len(videos)
                
                if total == 0:
                    print("\n[AVISO] A ligação foi estabelecida, mas esta playlist está vazia ou é privada.")
                    return False
                
                print(f"\n[SUCESSO] Foram encontrados {total} vídeos nesta playlist!")
                print(f"[3/3] A guardar os links no ficheiro '{nome_arquivo_saida}'...")
                
                with open(nome_arquivo_saida, 'w', encoding='utf-8') as f:
                    for idx, video in enumerate(videos, 1):
                        if video:
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
                print("\n[AVISO] Não foi possível ler os vídeos. A playlist é privada ou inexistente.")
                return False
                
    except Exception as e:
        print(f"\n[ERRO] Ocorreu uma falha na extração:")
        print(f"Detalhes: {e}")
        print("\nDicas para resolver:")
        print("1. Certifique-se de que a playlist está definida como 'Pública' ou 'Não Listada' no YouTube.")
        print("2. Verifique se copiou o link inteiro da barra de endereços.")
        return False

if __name__ == "__main__":
    # Descobre a pasta real onde o script 'extrair_playlist.py' está guardado
    PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
    PASTA_PLAYLISTS = os.path.join(PASTA_DO_SCRIPT, "Playlists")

    # Garante de forma totalmente automatizada que a pasta 'Playlists' existe na pasta correta
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
            # Pergunta o nome desejado para o arquivo (ex: Sertanejo)
            nome_categoria = input("\nQual o nome desta categoria? (ex: Casamentos, Eletronica, Musicas):\n> ").strip()
            
            # Limpa caracteres inválidos para nomes de arquivos no Windows
            nome_categoria_limpo = re.sub(r'[\\/*?:"<>|]', "", nome_categoria)
            if not nome_categoria_limpo:
                nome_categoria_limpo = "categoria_sem_nome"
            
            # Define o caminho absoluto para gravação sempre dentro da pasta Playlists correta
            nome_arquivo_saida = os.path.join(PASTA_PLAYLISTS, f"{nome_categoria_limpo}.txt")
                
            # Executa a extração
            extrair_links_playlist(url, nome_arquivo_saida)
            
        # Pergunta se o utilizador quer processar outra playlist
        opcao = input("\nQuer extrair outra playlist? Escreva S para Sim, ou pressione apenas ENTER para sair:\n> ").strip().upper()
        if opcao != 'S':
            print("\n=========================================")
            print("Extrator finalizado! Agora execute o seu 'gerar_catalogo.py' para atualizar o site.")
            input("Pressione a tecla [ENTER] para fechar esta janela...")
            break