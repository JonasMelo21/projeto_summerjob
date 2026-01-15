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

    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, '..', 'data')
    master_csv = os.path.join(data_path, 'base_professores.csv')
    
    # 1. Carrega ou Cria a Base Mestra
    if os.path.exists(master_csv):
        df_master = pd.read_csv(master_csv)
        print(f"✅ Base de dados carregada: {len(df_master)} professores.")
    else:
        print("⚠️ Base de dados não encontrada. Execute src/migrate_to_master.py primeiro ou certifique-se que o arquivo existe.")
        return

    # 2. Verifica se há arquivos de 'novos' para processar (Opcional - Fluxo de Ingestão)
    # Por enquanto, vamos assumir que queremos processar o que está FALTANDO na base mestra
    # ou se o usuário adicionar um arquivo 'novos_professores.csv', nós mesclamos.
    
    arquivos_novos = glob.glob(os.path.join(data_path, 'novos_*.csv'))
    if arquivos_novos:
        print(f"📥 Encontrados {len(arquivos_novos)} arquivos de novos dados para ingestão.")
        dfs_novos = []
        for f in arquivos_novos:
            try:
                df_temp = pd.read_csv(f)
                # Normalização básica de colunas
                col_map = {c: c.capitalize() for c in df_temp.columns} # Ex: website -> Website
                df_temp = df_temp.rename(columns=col_map)
                dfs_novos.append(df_temp)
            except: pass
            
        if dfs_novos:
            df_novos = pd.concat(dfs_novos)
            # Mescla com a master, removendo duplicatas pelo Website
            df_combined = pd.concat([df_master, df_novos])
            
            # Remove duplicatas (mantendo o que já tinhamos na master preferencialmente, ou o novo se atualizar)
            # Vamos manter o que tem mais informação. Se o da master já tem FIT, mantem a master.
            # Lógica simplificada: Drop duplicates pelo Website
            df_combined = df_combined.drop_duplicates(subset=['Website'], keep='first')
            
            if len(df_combined) > len(df_master):
                print(f"➕ Adicionados {len(df_combined) - len(df_master)} novos professores à base.")
                df_master = df_combined
                df_master.to_csv(master_csv, index=False) # Salva estado atualizado
    
    # 3. Identifica processamento pendente na Base Mestra
    # Critério: Fit é NaN ou vazio E Website é válido
    # Garante colunas
    if 'Fit' not in df_master.columns: df_master['Fit'] = None
    if 'Justificativa' not in df_master.columns: df_master['Justificativa'] = None

    # Função auxiliar para verificar se precisa processar
    def precisa_analisar(row):
        fit = str(row['Fit']).strip().lower()
        if fit in ['nan', 'none', '', 'erro']:
            return True
        return False

    mask_pendentes = df_master.apply(precisa_analisar, axis=1)
    df_pendentes = df_master[mask_pendentes]
    
    if df_pendentes.empty:
        print("🎉 Todos os professores da base já foram analisados!")
        return

    print(f"🔨 Iniciando análise para {len(df_pendentes)} professores pendentes...\n")
    
    alteracoes = False
    total = len(df_pendentes)
    
    # Itera apenas sobre os pendentes
    for count, (index, row) in enumerate(df_pendentes.iterrows()):
        site = row['Website']
        nome = row.get('Professor', 'Desconhecido')
        
        print(f"[{count+1}/{total}] Analisando {nome}...", end='\r')
        
        if pd.isna(site) or "http" not in str(site):
            print(f"\n   ⏩ Pulo: URL inválida ({site})")
            continue

        texto_site = scrape_website(site)
        
        if not texto_site:
            print(f"\n   ⚠️ Falha ao ler site: {site}")
            df_master.at[index, 'Justificativa'] = "Erro ao acessar site"
            df_master.at[index, 'Fit'] = "Erro"
            alteracoes = True
            try:
                df_master.to_csv(master_csv, index=False)
            except: pass
            continue
        
        try:
            relatorio, fit_categoria = analyze_profile(texto_site)
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "quota" in err_str or "resource exhausted" in err_str:
                print(f"\n✋ Cota excedida detectada! Salvando progresso e parando o script.")
                df_master.to_csv(master_csv, index=False)
                return # Encerra o processamento
            else:
                print(f"\n   ❌ Erro inesperado ao analisar perfil: {e}")
                relatorio = f"Erro na análise: {e}"
                fit_categoria = "Erro"
        
        if fit_categoria == "Erro":
            print(f"\n   ❌ Erro na API do Gemini para {site}")
            # Se deu erro no Gemini, também queremos salvar o status de erro se ele retornou algo
        
        df_master.at[index, 'Justificativa'] = relatorio
        df_master.at[index, 'Fit'] = fit_categoria
        alteracoes = True

        # SALVAMENTO INCREMENTAL (Segurança contra falhas/Ctrl+C)
        try:
            df_master.to_csv(master_csv, index=False)
            # print(f"      💾 Progresso salvo.")
        except Exception as save_err:
            print(f"      ❌ Erro ao salvar progresso: {save_err}")
        
        # Delay (Rate Limit)
        import time
        time.sleep(10) # Aumentei de 5 pra 10 pra dar mais fôlego à conta free

    print("")
    if alteracoes:
        df_master.to_csv(master_csv, index=False)
        print(f"💾 Base de dados atualizada com sucesso: {master_csv}")
    
    # Não precisa mais consolidar, pois já trabalhamos na base única

# Função consolidar removida pois obsoleta

if __name__ == "__main__":
    carregar_e_processar_dados()
