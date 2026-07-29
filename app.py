import streamlit as st
import pandas as pd
import plotly.express as px
import os
import math

# 1. Configuração da página (DEVE ser a PRIMEIRA chamada do Streamlit!)
st.set_page_config(
    page_title="Gestor de Aportes Inteligente",
    page_icon="📊",
    layout="wide"
)

# Arquivo para persistência local
CACHE_FILE = "carteira_atual.csv"

# 2. Título do Dashboard
st.title("📊 Gestor de Aportes Inteligente")
st.caption("Sprint 1: Ingestão de Dados e Visualização do Patrimônio")

# 3. Barra Lateral (Sidebar) - Ingestão de Dados
st.sidebar.header("Ingestão de Dados")
uploaded_file = st.sidebar.file_uploader("Carregue seu arquivo CSV da carteira", type=["csv"])
importar_btn = st.sidebar.button("Importar")

# 1. Se o usuário fizer upload e clicar em Importar -> Salva localmente e atualiza a sessão
if uploaded_file is not None and importar_btn:
    try:
        df = pd.read_csv(uploaded_file, sep=";", encoding="utf-8-sig")
        df.to_csv(CACHE_FILE, sep=";", index=False, encoding="utf-8-sig")  # Salva em disco
        st.session_state['df_carteira'] = df
        st.sidebar.success("Dados importados e salvos com sucesso!")
    except Exception as e:
        st.sidebar.error(f"Erro ao processar arquivo: {e}")

# 2. Se der F5 e o session_state estiver vazio, tenta carregar o arquivo salvo em disco
elif 'df_carteira' not in st.session_state and os.path.exists(CACHE_FILE):
    try:
        df = pd.read_csv(CACHE_FILE, sep=";", encoding="utf-8-sig")
        st.session_state['df_carteira'] = df
    except Exception as e:
        st.sidebar.error(f"Erro ao carregar cache local: {e}")

# 4. Exibição Principal (Apenas executa se houver dados no session_state)
if 'df_carteira' in st.session_state:
    df = st.session_state['df_carteira'].copy()

    # --- TRATAMENTO E TRATATIVA DE VALORES ---
    colunas_saldo = [c for c in df.columns if 'Saldo' in c]
    
    if colunas_saldo:
        col_saldo = colunas_saldo[0]
        if df[col_saldo].dtype == 'object':
            df['Saldo_Num'] = (
                df[col_saldo]
                .astype(str)
                .str.replace("R$", "", regex=False)
                .str.replace("US$", "", regex=False)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
                .str.strip()
            )
            df['Saldo_Num'] = pd.to_numeric(df['Saldo_Num'], errors='coerce').fillna(0)
        else:
            df['Saldo_Num'] = df[col_saldo]
    else:
        df['Saldo_Num'] = 0

    patrimonio_total = df['Saldo_Num'].sum()

    # --- CARDS DE DESTAQUE ---
    st.subheader("📊 Resumo Geral")
    col1, col2, col3 = st.columns(3)

    # Garantia de valor numérico válido
    try:
        patrimonio_total = float(patrimonio_total)
        if math.isnan(patrimonio_total):
            patrimonio_total = 0.0
    except (ValueError, TypeError):
        patrimonio_total = 0.0

    # Formatação em BRL
    patrimonio_fmt = f"R$ {patrimonio_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    col1.metric(label="Patrimônio Total", value=patrimonio_fmt)
    col2.metric(label="Total de Posições", value=f"{len(df)} ativos")

    if 'Tipo de ativo' in df.columns:
        maior_classe = df.groupby('Tipo de ativo')['Saldo_Num'].sum().idxmax()
        col3.metric(label="Maior Classe", value=maior_classe)

    st.divider()

    # --- GRÁFICOS DO SPRINT 1 ---
    st.subheader("📈 Distribuição do Patrimônio")
    col_left, col_right = st.columns(2)

    with col_left:
        if 'Tipo de ativo' in df.columns:
            df_classe = df.groupby('Tipo de ativo')['Saldo_Num'].sum().reset_index()
            fig_donut = px.pie(
                df_classe, 
                names='Tipo de ativo', 
                values='Saldo_Num', 
                hole=0.45,
                title="Alocação Atual por Classe de Ativo"
            )
            fig_donut.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_donut, use_container_width=True)

    with col_right:
        if '% Carteira' in df.columns and '% Ideal' in df.columns:
            # Tratamento caso os percentuais venham como string ("10%")
            for p_col in ['% Carteira', '% Ideal']:
                if df[p_col].dtype == 'object':
                    df[p_col] = df[p_col].astype(str).str.replace("%", "").str.replace(",", ".").str.strip()
                    df[p_col] = pd.to_numeric(df[p_col], errors='coerce').fillna(0)

            df_comparativo = df.groupby('Tipo de ativo')[['% Carteira', '% Ideal']].sum().reset_index()
            fig_bar = px.bar(
                df_comparativo,
                x='Tipo de ativo',
                y=['% Carteira', '% Ideal'],
                barmode='group',
                title="Alocação Atual vs. Meta Ideal (%)",
                labels={'value': 'Percentual (%)', 'variable': 'Legenda'}
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # --- TABELA DE POSIÇÕES DETALHADAS ---
    st.subheader("📋 Posições Atuais da Carteira")
    
    # Tratamento visual de 'None' / NaNs para a exibição da tabela
    df_display = df.drop(columns=['Saldo_Num'], errors='ignore').copy()
    cols_format = ['Rentabilidade', 'Vacância', 'P/VP', 'DY']
    for col in cols_format:
        if col in df_display.columns:
            df_display[col] = df_display[col].fillna('-')

    st.dataframe(df_display, use_container_width=True)

else:
    # Estado inicial limpo
    st.info("👋 Nenhum dado carregado. Faça o upload do arquivo CSV na barra lateral e clique em **Importar**.")