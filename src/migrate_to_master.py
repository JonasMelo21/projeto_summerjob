import pandas as pd
import glob
import os

def migrate_to_master():
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, '..', 'data')
    master_path = os.path.join(data_path, 'base_professores.csv')
    
    # Arquivos antigos
    csv_files = glob.glob(os.path.join(data_path, 'professores_data*.csv'))
    
    if not csv_files:
        print("Nenhum arquivo antigo encontrado par migrar.")
        return

    print("📦 Unificando arquivos antigos...")
    dfs = []
    
    # Mapeamento de colunas para garantir padrão
    # Ajuste conforme os nomes reais nos seus CSVs
    col_mapping = {
        'nome': 'Professor',
        'professor': 'Professor',
        'university': 'Universidade',
        'universidade': 'Universidade',
        'area': 'Area',
        'website': 'Website',
        'email': 'Email',
        'fit': 'Fit',
        'analise_llm': 'Justificativa'
    }

    for f in csv_files:
        try:
            df = pd.read_csv(f)
            # Normaliza colunas do arquivo atual
            df.columns = df.columns.str.strip().str.lower()
            
            # Renomeia para o padrão
            df = df.rename(columns=col_mapping)
            
            # Seleciona apenas as colunas padrão (cria se não existir)
            cols_padrao = ['Professor', 'Universidade', 'Area', 'Website', 'Email', 'Fit', 'Justificativa']
            for c in cols_padrao:
                if c not in df.columns:
                    df[c] = None
            
            dfs.append(df[cols_padrao])
            print(f"   -> Lido {len(df)} registros de {os.path.basename(f)}")
            
        except Exception as e:
            print(f"❌ Erro ao ler {f}: {e}")

    if dfs:
        # Concatena tudo
        df_master = pd.concat(dfs, ignore_index=True)
        
        # Remove duplicatas baseadas no Website (ou Nome+Universidade se preferir)
        # Website é o identificador mais único geralmente
        len_antes = len(df_master)
        
        # Normaliza website para remover duplicatas (remove barra final, etc)
        df_master['Website_Clean'] = df_master['Website'].astype(str).str.strip().str.rstrip('/')
        df_master = df_master.drop_duplicates(subset=['Website_Clean'], keep='last')
        df_master = df_master.drop(columns=['Website_Clean'])
        
        len_depois = len(df_master)
        print(f"   -> Removidos {len_antes - len_depois} duplicados.")

        # Salva a nova base mestra
        df_master.to_csv(master_path, index=False)
        print(f"✅ Base Mestra criada com sucesso: {master_path}")
        print(f"📊 Total de Professores Únicos: {len(df_master)}")
        
        print("\n⚠️  Recomendação: Mova os arquivos 'professores_data*.csv' para uma pasta de backup para não confundir.")
    else:
        print("Nenhum dado válido encontrado.")

if __name__ == "__main__":
    migrate_to_master()
