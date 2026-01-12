import pandas as pd
import os
import glob
import logging
from dotenv import load_dotenv
from scraper import scrape_website
from analyzer import analyze_profile

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def verificar_env():
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ ERRO: A variável de ambiente GEMINI_API_KEY não foi encontrada.")
        print(">> Crie um arquivo .env na raiz do projeto com o conteúdo:")
        print("GEMINI_API_KEY=sua_chave_aqui")
        return False
    return True

def carregar_e_processar_dados():
    if not verificar_env():
        return

    # Define o caminho para a pasta 'data'
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, '..', 'data')
    
    arquivos_csv = glob.glob(os.path.join(data_path, '*.csv'))
    
    if not arquivos_csv:
        print(f"⚠️  Nenhum arquivo CSV encontrado em: {os.path.abspath(data_path)}")
        return

    print(f"✅ Encontrados {len(arquivos_csv)} arquivos. Iniciando processamento...\n")

    for arquivo in arquivos_csv:
        # Pula arquivos que não são os originais e já foram consolidados
        if 'dados_consolidados' in arquivo:
            continue

        nome_arquivo = os.path.basename(arquivo)
        print(f"--- Processando: {nome_arquivo} ---")
        try:
            df = pd.read_csv(arquivo)
            
            # Normalizar nome das colunas (remover espaços, etc)
            df.columns = df.columns.str.strip()
            
            # Verifica se colunas necessárias existem ('Website')
            coluna_site = None
            for col in df.columns:
                if col.lower() == 'website':
                    coluna_site = col
                    break
            
            if not coluna_site:
                print(f"⚠️  Arquivo {nome_arquivo} ignorado: Coluna 'Website' não encontrada.")
                continue

            # Garante que as colunas de saída existam
            if 'fit' not in df.columns:
                df['fit'] = None
            if 'analise_llm' not in df.columns:
                df['analise_llm'] = None

            alteracoes = False
            total_linhas = len(df)
            
            for index, row in df.iterrows():
                site = row[coluna_site]
                
                # Barra de progresso visual simples no terminal
                print(f"[{index+1}/{total_linhas}] Analisando {row.get('Nome', 'Professor')}...", end='\r')
                
                # Se já tem fit preenchido, pula
                # Adicionei filtro para "Erro" -> Se deu erro antes, tenta de novo
                current_fit = str(row['fit']).strip() if pd.notna(row['fit']) else ""
                
                if current_fit and current_fit not in ["", "nan", "None", "Erro"]:
                     continue
                
                if pd.isna(site) or not isinstance(site, str) or "http" not in site:
                    # Só loga se não for nulo/vazio silencioso
                    if pd.notna(site):
                        print(f"\n   ⏩ Pulo: URL inválida ({site})")
                    continue

                # print(f"\n   🔍 Scraping: {site} ...") # Comentado para poluir menos, descomente para debug
                texto_site = scrape_website(site)
                
                if not texto_site:
                    print(f"\n      ⚠️ Falha ao ler site: {site}")
                    df.at[index, 'analise_llm'] = "Erro ao acessar site"
                    df.at[index, 'fit'] = "Erro"
                    alteracoes = True
                    continue
                
                # print("      🧠 Analisando com Gemini...")
                relatorio, fit_categoria = analyze_profile(texto_site)
                
                # Se retornou erro da API, mostramos no terminal
                if fit_categoria == "Erro":
                   print(f"\n      ❌ Erro na API do Gemini para {site}")
                
                df.at[index, 'analise_llm'] = relatorio
                df.at[index, 'fit'] = fit_categoria
                alteracoes = True
                # print(f"      ✅ Resultado: {fit_categoria}")

            print("") # Pula linha após o loop
            if alteracoes:
                # Salva o arquivo atualizado
                df.to_csv(arquivo, index=False)
                print(f"💾 Arquivo {nome_arquivo} atualizado com sucesso!\n")
            else:
                print(f"Distribuição de dados não alterada para {nome_arquivo}.\n")
            
        except Exception as e:
            print(f"❌ Erro ao processar {nome_arquivo}: {e}")
            logging.exception("Detalhes do erro:")
    
    # --- Nova Etapa: Consolidar Resultados ---
    consolidar_resultados(data_path)

def consolidar_resultados(data_path):
    print("\n📦 Consolidando resultados em um único arquivo...")
    try:
        arquivos_csv = glob.glob(os.path.join(data_path, '*.csv'))
        dfs = []
        
        for arquivo in arquivos_csv:
            # Ignora o próprio arquivo de resumo se ele já existir para não duplicar
            if 'dados_consolidados_professores.csv' in arquivo:
                continue
                
            try:
                df = pd.read_csv(arquivo)
                df.columns = df.columns.str.strip() # Normaliza colunas
                
                # Seleciona apenas colunas de interesse (normalizando nomes se necessário)
                # Vamos tentar encontrar as colunas independente de case
                col_map = {c.lower(): c for c in df.columns}
                
                cols_desired = {
                    'nome': 'Professor',
                    'area': 'Area',
                    'website': 'Website',
                    'fit': 'Fit',
                    'analise_llm': 'Justificativa'
                }
                
                df_temp = pd.DataFrame()
                
                for key, target_name in cols_desired.items():
                    if key in col_map:
                        df_temp[target_name] = df[col_map[key]]
                    else:
                        df_temp[target_name] = None
                        
                # Adiciona apenas se tiver 'Fit' preenchido (opcional, mas o user quer "os que tenho fit")
                # Mas vamos pegar todos para o dashboard filtrar
                dfs.append(df_temp)
                
            except Exception as e:
                print(f"Erro ao ler {arquivo} para consolidação: {e}")

        if dfs:
            df_final = pd.concat(dfs, ignore_index=True)
            
            # Ordenar por Fit (opcional)
            # Vamos criar uma coluna numérica auxiliar para ordenação
            fit_order = {
                "Fit Muito Alto": 0,
                "Fit Alto": 1,
                "Fit Baixo": 2,
                "Fit Muito Baixo": 3,
                "Erro": 99,
                "N/A": 99
            }
            df_final['rank'] = df_final['Fit'].map(fit_order).fillna(99)
            df_final = df_final.sort_values('rank').drop('rank', axis=1)
            
            output_path = os.path.join(data_path, 'dados_consolidados_professores.csv')
            df_final.to_csv(output_path, index=False)
            print(f"✅ Arquivo consolidado criado em: {os.path.abspath(output_path)}")
        else:
            print("⚠️ Nenhum dado para consolidar.")
            
    except Exception as e:
        print(f"❌ Erro na consolidação: {e}")

if __name__ == "__main__":
    carregar_e_processar_dados()
