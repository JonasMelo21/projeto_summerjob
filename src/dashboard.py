import streamlit as st
import pandas as pd
import os

# Configuração da Página
st.set_page_config(
    page_title="Summer Job Matcher",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS Personalizado
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    # Caminho do arquivo consolidado
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, '..', 'data', 'dados_consolidados_professores.csv')
    
    if not os.path.exists(data_path):
        return None
    
    df = pd.read_csv(data_path)
    return df

def main():
    st.title("🎓 Professor Research Fit Explorer")
    st.markdown("Análise de compatibilidade para vagas de Summer/Winter Job baseada em **Interesses de Pesquisa** e **Perfil do Candidato**.")

    df = load_data()

    if df is None:
        st.warning("⚠️ Arquivo de dados não encontrado. Execute o script `src/main.py` primeiro para gerar as análises.")
        return

    # Sidebar - Filtros
    st.sidebar.header("Filtros")
    
    # Filtro de Fit
    opcoes_fit = df['Fit'].unique().tolist()
    # Tenta ordenar opções de forma lógica
    ordem_logica = ["Fit Muito Alto", "Fit Alto", "Fit Baixo", "Fit Muito Baixo", "Erro", "N/A"]
    opcoes_fit_sorted = [x for x in ordem_logica if x in opcoes_fit] + [x for x in opcoes_fit if x not in ordem_logica]
    
    selected_fits = st.sidebar.multiselect("Filtrar por Nível de Fit", options=opcoes_fit_sorted, default=opcoes_fit_sorted)
    
    # Filtro de Área
    if 'Area' in df.columns:
        all_areas = set()
        for x in df['Area'].dropna():
            all_areas.update([a.strip() for a in str(x).split(',')])
        selected_area = st.sidebar.multiselect("Filtrar por Área de Interesse", options=sorted(list(all_areas)))
    else:
        selected_area = []

    # Aplicação dos Filtros
    df_filtered = df[df['Fit'].isin(selected_fits)]
    
    if selected_area:
        # Filtra se a area do professor contem qualquer uma das selecionadas
        mask = df_filtered['Area'].apply(lambda x: any(area in str(x) for area in selected_area))
        df_filtered = df_filtered[mask]

    # Métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Professores (Filtrado)", len(df_filtered))
    
    high_fit_count = len(df_filtered[df_filtered['Fit'].isin(['Fit Muito Alto', 'Fit Alto'])])
    col2.metric("Oportunidades de Alto Fit", high_fit_count)
    
    processed_percent = 100 # Assumindo 100% pois lemos do arquivo consolidado
    col3.metric("Análise Completada", f"{processed_percent}%")

    st.markdown("---")

    # Exibição Principal (Tabela Interativa)
    if not df_filtered.empty:
        # Configurar link clicável na tabela é chatinho no st.dataframe padrão, 
        # mas vamos usar st.data_editor com column_config para ficar TOP
        
        st.subheader("📋 Lista de Professores")
        
        st.data_editor(
            df_filtered,
            column_config={
                "Website": st.column_config.LinkColumn("Website Link", display_text="Visitar Perfil"),
                "Justificativa": st.column_config.TextColumn("Análise da IA", width="large"),
                "Fit": st.column_config.Column(
                    "Nível de Compatibilidade",
                    width="medium",
                    help="Classificação gerada pela IA",
                ),
            },
            hide_index=True,
            use_container_width=True,
            disabled=True # Tabela apenas leitura
        )
        
        # Detalhes Expandidos (Opcional, para ler a justificativa completa com calma)
        st.markdown("### 🔍 Detalhes da Análise")
        prof_selecionado = st.selectbox("Selecione um professor para ver o relatório completo:", df_filtered['Professor'].unique())
        
        if prof_selecionado:
            row = df_filtered[df_filtered['Professor'] == prof_selecionado].iloc[0]
            
            with st.expander(f"Ver Análise Completa de **{prof_selecionado}**", expanded=True):
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.info(f"**Fit:** {row['Fit']}")
                    st.write(f"**Área:** {row['Area']}")
                    st.write(f"**Link:** [Acessar Página]({row['Website']})")
                with c2:
                    st.markdown("#### Relatório da IA")
                    st.write(row['Justificativa'])
                    
    else:
        st.info("Nenhum professor encontrado com os filtros selecionados.")

if __name__ == "__main__":
    main()
