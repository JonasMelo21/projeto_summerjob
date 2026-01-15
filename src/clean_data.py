import pandas as pd
import glob
import os

def clean_manual_fits():
    # Caminho para a pasta data
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, '..', 'data')
    
    # Pega apenas os arquivos de dados brutos, não o consolidado
    csv_files = glob.glob(os.path.join(data_path, 'professores_data*.csv'))
    
    # Lista de valores manuais antigos que queremos remover (tudo em minúsculo para comparação)
    valores_para_remover = [
        "high", "very high", "veryhigh", 
        "low", "very low", "verylow", 
        "medium", "fit medium"
    ]

    print(f"🔍 Iniciando limpeza em {len(csv_files)} arquivos...\n")

    for file_path in csv_files:
        nome_arquivo = os.path.basename(file_path)
        try:
            df = pd.read_csv(file_path)
            
            # Se não tiver coluna fit, pula
            coluna_fit = None
            for col in df.columns:
                if col.lower().strip() == 'fit':
                    coluna_fit = col
                    break
            
            if not coluna_fit:
                print(f"⚠️ {nome_arquivo}: Coluna 'fit' não encontrada.")
                continue

            # Função de limpeza
            def limpar_valor(val):
                if pd.isna(val):
                    return val
                
                val_str = str(val).strip().lower()
                
                # Se for um dos valores manuais, retorna None (vazio)
                if val_str in valores_para_remover:
                    return None
                
                # Se for "fit alto", "fit baixo" (gerados pela IA), mantém
                # Se for string vazia, mantém
                return val

            # Conta preenchidos antes
            total_antes = df[coluna_fit].notna().sum()
            
            # Aplica a limpeza
            df[coluna_fit] = df[coluna_fit].apply(limpar_valor)
            
            # Conta preenchidos depois
            total_depois = df[coluna_fit].notna().sum()
            removidos = total_antes - total_depois

            if removidos > 0:
                print(f"✅ {nome_arquivo}: Convertidos {removidos} registros manuais para vazios.")
                # Também limpa a justificativa se o fit foi limpo, para garantir reanálise completa
                # (Assumindo que se limpamos o fit, queremos nova justificativa também)
                
                # Verifica coluna de justificativa/analise_llm
                col_just = 'analise_llm' if 'analise_llm' in df.columns else None
                if col_just:
                    # Onde fit ficou nulo, anula a justificativa também
                    mask_limpos = df[coluna_fit].isna()
                    df.loc[mask_limpos, col_just] = None
                
                df.to_csv(file_path, index=False)
            else:
                print(f"ℹ️ {nome_arquivo}: Nenhum valor manual ('High'/'Low') encontrado.")

        except Exception as e:
            print(f"❌ Erro ao processar {nome_arquivo}: {e}")

if __name__ == "__main__":
    clean_manual_fits()
