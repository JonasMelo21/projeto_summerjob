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
    # Caminho do arquivo MESTRE
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, '..', 'data', 'base_professores.csv')
    
    if not os.path.exists(data_path):
        st.error(f"Arquivo não encontrado: {data_path}")
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

    # Filtro de Universidade
    if 'Universidade' in df.columns:
        all_unis = sorted(list({str(x).strip() for x in df['Universidade'].dropna()}))
        selected_unis = st.sidebar.multiselect("Filtrar por Universidade", options=all_unis)
    else:
        selected_unis = []

    # Aplicação dos Filtros
    df_filtered = df[df['Fit'].isin(selected_fits)]
    
    if selected_area:
        # Filtra se a area do professor contem qualquer uma das selecionadas
        mask = df_filtered['Area'].apply(lambda x: any(area in str(x) for area in selected_area))
        df_filtered = df_filtered[mask]

    if selected_unis:
         df_filtered = df_filtered[df_filtered['Universidade'].isin(selected_unis)]

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
        
        column_config = {
            "Website": st.column_config.LinkColumn("Website"),
            "Justificativa": st.column_config.TextColumn("Análise LLM", width="large"),
            "Fit": st.column_config.TextColumn("Nível de Fit", width="medium"),
            "Professor": st.column_config.TextColumn("Professor", width="medium"),
            "Universidade": st.column_config.TextColumn("Universidade", width="medium"),
            "Area": st.column_config.TextColumn("Área de Pesquisa", width="medium"),
        }
        
        # Reordenar colunas para ficar visualmente agradável
        cols_order = ['Professor', 'Universidade', 'Fit', 'Area', 'Website', 'Justificativa']
        # Garante que só usa colunas que existem
        cols_order = [c for c in cols_order if c in df_filtered.columns]
        
        st.dataframe(
            df_filtered[cols_order],
            column_config=column_config,
            hide_index=True,
            use_container_width=True
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
