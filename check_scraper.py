import sys
import os

# Adiciona o diretório src ao path para poder importar o scraper
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.append(src_path)

from scraper import scrape_website

def teste_real():
    print("🕵️  Teste de Visão do Scraper")
    
    # Se passar URL como argumento, usa ela. Senão pede input.
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        try:
            url = input("Cole a URL do site do professor aqui: ").strip()
        except EOFError:
            print("Erro: Nenhuma entrada recebida.")
            return

    if not url:
        print("URL vazia.")
        return

    print(f"\n--- Acessando {url} ---")
    try:
        texto = scrape_website(url)
    except Exception as e:
        print(f"Erro crítico ao chamar scrape_website: {e}")
        return

    if not texto:
        print("❌ O scraper não conseguiu ler NADA (retornou vazio ou None).")
        print("Motivo provável: Site exige JavaScript, bloqueia bots ou URL inválida.")
    else:
        print(f"✅ Sucesso! Extraídos {len(texto)} caracteres.")
        print("\n--- O QUE A IA VAI LER (Primeiros 500 chars) ---")
        print(texto[:500])
        print("\n--- FIM DO PREVIEW ---")
        
        if len(texto) < 200:
            print("⚠️  ALERTA: O texto extraído é muito curto. Pode ser que o site não tenha carregado corretamente.")

if __name__ == "__main__":
    teste_real()
