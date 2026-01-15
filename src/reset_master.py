import pandas as pd
import os
import shutil

def reset_and_clean_master():
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, '..', 'data')
    master_csv = os.path.join(data_path, 'base_professores.csv')
    
    if not os.path.exists(master_csv):
        print("❌ Arquivo base_professores.csv não encontrado.")
        return

    # Backup antes de mexer
    shutil.copy(master_csv, master_csv + ".bak")
    print("📦 Backup criado: base_professores.csv.bak")

    df = pd.read_csv(master_csv)
    print(f"📊 Total de registros antes: {len(df)}")
    
    # Colunas que queremos resetar para forçar reanálise
    cols_to_reset = ['Fit', 'Justificativa']
    
    # 1. Limpa valores manuais antigos (High, Low, etc)
    # 2. Limpa valores atuais para forçar reprocessamento com novo scraper
    #    Vamos limpar TUDO para garantir que todos passem pelo novo scraper V2
    
    print("🧹 Limpando colunas 'Fit' e 'Justificativa' para reprocessamento total...")
    df['Fit'] = None
    df['Justificativa'] = None
    
    df.to_csv(master_csv, index=False)
    print("✅ Base resetada com sucesso! Rode 'uv run src/main.py' para reprocessar.")

if __name__ == "__main__":
    reset_and_clean_master()
