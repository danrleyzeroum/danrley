import os
import time
import requests
from supabase import create_client

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ptdghdduyuyswxgadfqa.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0ZGdoZGR1eXV5c3d4Z2FkZnFhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MzI5Njc2NiwiZXhwIjoyMTA4ODcyNzY2fQ.TyMFqqqC-g1elhej9s3Ofb293JH0H4XbK7AYxypy5-w")

# Credenciais da API Streamtape
STREAMTAPE_LOGIN = os.getenv("STREAMTAPE_LOGIN", "62467efddc84ae766938")
STREAMTAPE_KEY = os.getenv("STREAMTAPE_KEY", "9yzGKpgeejUYmj")

def extrair_file_id(url: str) -> str:
    """Extrai o código do ficheiro a partir do formato https://streamtape.com/e/ID/ ou /v/ID/"""
    if not url:
        return ""
    partes = url.strip().split('/')
    for separador in ['e', 'v']:
        if separador in partes:
            idx = partes.index(separador)
            if idx + 1 < len(partes):
                return partes[idx + 1]
    return ""

def executar_renovacao():
    print("=" * 60)
    print("Iniciando rotina de renovação de mídias do Streamtape...")
    print("=" * 60)

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("midias").select("id, titulo, video_url").execute()
        midias = response.data
    except Exception as e:
        print(f"Erro ao conectar com o Supabase: {e}")
        return

    total = len(midias)
    print(f"Total de conteúdos encontrados na base de dados: {total}\n")

    sucessos = 0
    falhas = 0

    for idx, item in enumerate(midias, 1):
        titulo = item.get("titulo", f"ID {item.get('id')}")
        video_url = item.get("video_url", "")

        file_id = extrair_file_id(video_url)
        if not file_id:
            print(f"[{idx}/{total}] [IGNORADO] '{titulo}' não possui URL de Streamtape válida.")
            continue

        try:
            # 1. Chamada oficial à API do Streamtape (renova a atividade do ficheiro e verifica integridade)
            api_endpoint = f"https://api.streamtape.com/file/info?file={file_id}&login={STREAMTAPE_LOGIN}&key={STREAMTAPE_KEY}"
            res_api = requests.get(api_endpoint, timeout=15).json()

            if res_api.get("status") == 200:
                # 2. Requisição leve de alcance (baixa apenas 1KB para registar tráfego real sem sobrecarga)
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Range": "bytes=0-1024"
                }
                requests.get(video_url, headers=headers, timeout=10)

                print(f"[{idx}/{total}] [RENOVADO COM SUCESSO] {titulo} (ID: {file_id})")
                sucessos += 1
            else:
                msg = res_api.get("msg", "Erro desconhecido")
                print(f"[{idx}/{total}] [ALERTA] {titulo} retornou erro no Streamtape: {msg}")
                falhas += 1

            # Pausa de 1 segundo para respeitar o limite de pedidos da API
            time.sleep(1)

        except Exception as erro:
            print(f"[{idx}/{total}] [FALHA] Erro ao processar '{titulo}': {erro}")
            falhas += 1

    print("\n" + "=" * 60)
    print(f"Relatório Final:")
    print(f"Processados: {total} | Sucessos: {sucessos} | Falhas: {falhas}")
    print("=" * 60)

if __name__ == "__main__":
    executar_renovacao()
