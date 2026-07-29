import streamlit as st
import pandas as pd
import plotly.express as px
import os
import math
import requests

# 1. Configuração da página (DEVE ser a PRIMEIRA chamada do Streamlit!)
st.set_page_config(
    page_title="Gestor de Aportes Inteligente",
    page_icon="📊",
    layout="wide"
)

# Arquivo para persistência local
CACHE_FILE = "carteira_atual.csv"

# --- FUNÇÕES AUXILIARES DE LIMPEZA DE DADOS ---
@st.cache_data(ttl=3600)  # Guarda a cotação em cache por 1 hora para economizar requisições
def obter_cotacao_dolar():
    """Busca a cotação atual do Dólar em tempo real usando a AwesomeAPI."""
    try:
        response = requests.get("https://economia.awesomeapi.com.br/json/last/USD-BRL", timeout=5)
        data = response.json()
        return float(data["USDBRL"]["bid"])
    except Exception:
        return 5.20  # Valor padrão de segurança caso ocorra erro na chamada

def parse_moeda(valor):
    """Converte valores monetários/formatados (R$ 1.234,56 ou 1234.56) em float numérico puro."""
    if pd.isna(valor) or valor == "" or valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    
    val_str = str(valor).strip()
    # Remove símbolos de moeda e caracteres não numéricos exceto vírgula e ponto
    val_str = val_str.replace("R$", "").replace("US$", "").replace("$", "").replace("%", "").strip()
    
    if not val_str:
        return 0.0

    # Lógica para tratar notação brasileira (1.234,56) vs internacional (1,234.56)
    if "," in val_str and "." in val_str:
        if val_str.rfind(",") > val_str.rfind("."):
            # Padrão BR: 1.234,56 -> 1234.56
            val_str = val_str.replace(".", "").replace(",", ".")
        else:
            # Padrão US: 1,234.56 -> 1234.56
            val_str = val_str.replace(",", "")
    elif "," in val_str:
        # Apenas vírgula: 1234,56 -> 1234.56
        val_str = val_str.replace(",", ".")

    try:
        return float(val_str)
    except ValueError:
        return 0.0

# 2. Título do Dashboard
st.title("📊 Gestor de Aportes Inteligente")
st.caption("Sprint 1: Ingestão de Dados e Visualização do Patrimônio")

# 3. Barra Lateral (Sidebar) - Ingestão de Dados
st.sidebar.header("Ingestão de Dados")
uploaded_file = st.sidebar.file_uploader("Carregue seu arquivo CSV da carteira", type=["csv"])
importar_btn = st.sidebar.button("Importar / Processar", type="primary")

# Chamada e exibição da cotação do dólar
cotacao_dolar = obter_cotacao_dolar()
st.sidebar.info(f"💵 Cotação USD/BRL: **R$ {cotacao_dolar:.2f}**")

# Botão para resetar dados salvos
if st.sidebar.button("🗑️ Limpar Carteira Salva"):
    if 'df_carteira' in st.session_state:
        del st.session_state['df_carteira']
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception:
            pass
    st.sidebar.warning("Cache e sessão limpos!")
    st.rerun()

# 4. Processamento quando o usuário envia um novo CSV via uploader
if uploaded_file is not None and importar_btn:
    try:
        nome_arquivo = uploaded_file.name
        try:
            df_raw = pd.read_csv(uploaded_file, sep=";", encoding="utf-8-sig")
            if len(df_raw.columns) <= 1:
                uploaded_file.seek(0)
                df_raw = pd.read_csv(uploaded_file, sep=",", encoding="utf-8-sig")
        except Exception:
            uploaded_file.seek(0)
            df_raw = pd.read_csv(uploaded_file, sep=",", encoding="utf-8-sig")

        df_raw.to_csv(CACHE_FILE, sep=";", index=False, encoding="utf-8-sig")
        st.session_state['df_carteira'] = df_raw
        st.sidebar.success("Dados importados e salvos com sucesso!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Erro ao processar arquivo: {e}")


# 6. Exibição Principal (Apenas executa se houver dados)
if 'df_carteira' in st.session_state and not st.session_state['df_carteira'].empty:
    df = st.session_state['df_carteira'].copy()

    # --- IDENTIFICAÇÃO E TRATAMENTO FLEXÍVEL DE COLUNAS ---
    col_classe = next((c for c in ['Tipo de ativo', 'Tipo', 'Classe', 'Categoria'] if c in df.columns), None)
    col_saldo_orig = next((c for c in df.columns if 'Saldo' in c or 'Valor Total' in c or 'Patrimônio' in c), None)

    if col_saldo_orig:
        df['Saldo_Num'] = df[col_saldo_orig].apply(parse_moeda)
    else:
        df['Saldo_Num'] = 0.0

    col_perc_carteira = next((c for c in df.columns if '% Carteira' in c or 'Carteira (%)' in c or '% Atual' in c), None)
    col_perc_ideal = next((c for c in df.columns if '% Ideal' in c or 'Meta (%)' in c or '% Meta' in c), None)

    if col_perc_carteira:
        df['% Carteira_Num'] = df[col_perc_carteira].apply(parse_moeda)
    else:
        df['% Carteira_Num'] = 0.0

    def converter_saldo_brl(row):
        saldo = row['Saldo_Num']
        tipo = str(row[col_classe]).strip() if col_classe and col_classe in df.columns else ""
        if tipo in ['Stocks', 'ETFs Intern.']:
            return saldo * cotacao_dolar
        return saldo

    df['Saldo_Num'] = df.apply(converter_saldo_brl, axis=1)

    if col_perc_ideal:
        df['% Ideal_Num'] = df[col_perc_ideal].apply(parse_moeda)
    else:
        df['% Ideal_Num'] = 0.0

    patrimonio_total = df['Saldo_Num'].sum()
    if patrimonio_total > 0:
        df['% Carteira_Num'] = (df['Saldo_Num'] / patrimonio_total) * 100
    else:
        df['% Carteira_Num'] = 0.0

    # --- CARDS DE DESTAQUE ---
    st.subheader("📊 Resumo Geral")
    col1, col2, col3 = st.columns(3)

    patrimonio_fmt = f"R$ {patrimonio_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    col1.metric(label="Patrimônio Total", value=patrimonio_fmt)
    col2.metric(label="Total de Posições", value=f"{len(df)} ativos")

    if col_classe and col_classe in df.columns:
        df_agrupado_classe = df.groupby(col_classe)['Saldo_Num'].sum()
        if not df_agrupado_classe.empty and df_agrupado_classe.sum() > 0:
            maior_classe = df_agrupado_classe.idxmax()
        else:
            maior_classe = "N/A"
        col3.metric(label="Maior Classe", value=str(maior_classe))
    else:
        col3.metric(label="Maior Classe", value="N/A")

    st.divider()

    # --- GRÁFICOS DO SPRINT 1 ---
    st.subheader("📈 Distribuição do Patrimônio")
    col_left, col_right = st.columns(2)

    with col_left:
        if col_classe and col_classe in df.columns and patrimonio_total > 0:
            df_classe = df.groupby(col_classe)['Saldo_Num'].sum().reset_index()
            fig_donut = px.pie(
                df_classe, 
                names=col_classe, 
                values='Saldo_Num', 
                hole=0.45,
                title="Alocação Atual por Classe de Ativo",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_donut.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("Aguardando dados válidos para exibir o gráfico de rosca.")

    with col_right:
        if col_classe and col_classe in df.columns:
            df_comparativo = df.groupby(col_classe)[['% Carteira_Num', '% Ideal_Num']].sum().reset_index()
            df_comparativo.columns = [col_classe, '% Carteira', '% Ideal']

            fig_bar = px.bar(
                df_comparativo,
                x=col_classe,
                y=['% Carteira', '% Ideal'],
                barmode='group',
                title="Alocação Atual vs. Meta Ideal (%)",
                labels={'value': 'Percentual (%)', 'variable': 'Legenda', col_classe: 'Tipo de Ativo'},
                color_discrete_sequence=['#1f77b4', '#aec7e8']
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Aguardando dados válidos para exibir o gráfico de barras.")

    st.divider()

    # --- TABELA DE POSIÇÕES DETALHADAS ---
    st.subheader("📋 Posições Atuais da Carteira")
    
    df_display = df.drop(columns=['Saldo_Num', '% Carteira_Num', '% Ideal_Num'], errors='ignore').copy()
    df_display = df_display.fillna('-')

    st.dataframe(df_display, use_container_width=True)

else:
    st.info("👋 Nenhum dado carregado. Faça o upload do arquivo CSV na barra lateral e clique em **Importar / Processar**.")