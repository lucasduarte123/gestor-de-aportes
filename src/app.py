import json
import math
import os
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import yfinance as yf

# 1. Configuração da página (DEVE ser a PRIMEIRA chamada do Streamlit!)
st.set_page_config(
    page_title="Gestor de Aportes Inteligente", page_icon="📊", layout="wide"
)


@st.cache_data
def carregar_dados_b3():
  caminho = "data/b3.json"
  if not os.path.exists(caminho):
    return {}

  with open(caminho, "r", encoding="utf-8") as f:
    return json.load(f)


# Carrega os dados da B3
dados_b3 = carregar_dados_b3()

# Exemplo de como acessar as ações e FIIs na barra lateral
st.sidebar.markdown("---")
st.sidebar.header("📊 Mercado B3")

if dados_b3:
  assets_dict = dados_b3.get("assets", {})
  if "stocks" in assets_dict:
    df_stocks = pd.DataFrame(assets_dict["stocks"])
    if not df_stocks.empty and "issuingCompany" in df_stocks.columns:
      ticker_escolhido = st.sidebar.selectbox(
          "Selecione uma Ação", options=df_stocks["issuingCompany"].tolist()
      )
      st.sidebar.write(f"Selecionado: **{ticker_escolhido}**")

# Arquivo para persistência local
CACHE_FILE = "carteira_atual.csv"

# Função para buscar o preço atual na B3 via yfinance
def buscar_preco_atual(ticker):
    try:
        # Ativos da B3 precisam do sufixo .SA (ex: VGIR11.SA, PETR4.SA)
        simbolo = ticker.strip().upper()
        if not simbolo.endswith(".SA") and len(simbolo) > 4:
            simbolo_b3 = simbolo + ".SA"
        else:
            simbolo_b3 = simbolo
            
        dados = yf.Ticker(simbolo_b3)
        hist = dados.history(period="1d")
        
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
        
        # Tentativa alternativa sem o .SA caso falhe
        if simbolo_b3 != simbolo:
            hist_alt = yf.Ticker(simbolo).history(period="1d")
            if not hist_alt.empty:
                return float(hist_alt['Close'].iloc[-1])
                
        return 0.0
    except Exception:
        return 0.0

# --- FUNÇÕES AUXILIARES DE LIMPEZA E ENRIQUECIMENTO ---
@st.cache_data(ttl=3600)
def enriquecer_carteira(df_usuario, dados_b3_json):
  """Recebe um DataFrame com colunas ['Ativo', 'Quant.']

  e enriquece com cotações de mercado e classificações da B3.
  """
  carteira_enriquecida = []
  temp_list = []
  patrimonio_total = 0.0

  for _, row in df_usuario.iterrows():
    ticker = str(row["Ativo"]).strip().upper()
    quant = float(row["Quant."])

    # Busca cotação atual no Yahoo Finance usando o sufixo .SA da B3
    ticker_yf = f"{ticker}.SA"
    preco_atual = 0.0
    try:
      dados_ticker = yf.Ticker(ticker_yf)
      hist = dados_ticker.history(period="1d")
      if not hist.empty:
        preco_atual = float(hist["Close"].iloc[-1])
    except Exception:
      preco_atual = 0.0

    saldo = quant * preco_atual
    patrimonio_total += saldo

    temp_list.append({
        "Tipo de ativo": "Ações/FIIs",
        "Ativo": ticker,
        "Quant.": quant,
        "Preço Médio": preco_atual,
        "Preço Atual": preco_atual,
        "Saldo_Num": saldo,
        "Nota": 10,
        "Ideal_Num": 1.2,
    })

  for item in temp_list:
    saldo = item["Saldo_Num"]
    pct_carteira = (
        (saldo / patrimonio_total * 100) if patrimonio_total > 0 else 0.0
    )
    comprar = "Sim" if pct_carteira < item["Ideal_Num"] else "Não"

    carteira_enriquecida.append({
        "Tipo de ativo": item["Tipo de ativo"],
        "Ativo": item["Ativo"],
        "Quant.": item["Quant."],
        "Preço Médio": f"R$ {item['Preço Médio']:.2f}",
        "Preço Atual": f"R$ {item['Preço Atual']:.2f}",
        "Variação": "0,00%",
        "Rentabilidade": "0,00%",
        "Vacância": "0,00%",
        "Saldo": f"R$ {saldo:.2f}",
        "Saldo_Num": saldo,  # Coluna auxiliar para cálculos
        "P/VP": 1.0,
        "DY": "0,00%",
        "Nota": item["Nota"],
        "% Carteira": f"{pct_carteira:.2f}%",
        "% Carteira_Num": pct_carteira,  # Coluna auxiliar para gráficos
        "% Ideal": f"{item['Ideal_Num']:.2f}%",
        "% Ideal_Num": item["Ideal_Num"],  # Coluna auxiliar para gráficos
        "Comprar?": comprar,
    })

  return pd.DataFrame(carteira_enriquecida)


def obter_cotacao_dolar():
  """Busca a cotação atual do Dólar em tempo real usando a AwesomeAPI."""
  try:
    response = requests.get(
        "https://economia.awesomeapi.com.br/json/last/USD-BRL", timeout=5
    )
    data = response.json()
    return float(data["USDBRL"]["bid"])
  except Exception:
    return 5.20


def parse_moeda(valor):
  """Converte valores monetários/formatados em float numérico puro."""
  if pd.isna(valor) or valor == "" or valor is None:
    return 0.0
  if isinstance(valor, (int, float)):
    return float(valor)

  val_str = str(valor).strip()
  val_str = (
      val_str.replace("R$", "")
      .replace("US$", "")
      .replace("$", "")
      .replace("%", "")
      .strip()
  )

  if not val_str:
    return 0.0

  if "," in val_str and "." in val_str:
    if val_str.rfind(",") > val_str.rfind("."):
      val_str = val_str.replace(".", "").replace(",", ".")
    else:
      val_str = val_str.replace(",", "")
  elif "," in val_str:
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

# Orientação clara para o usuário sobre o formato esperado
st.sidebar.markdown(
    "O arquivo deve conter as colunas obrigatórias:\n"
    "- **Ativo** (Ex: *PETR4*, *VALE3*, *HGLG11*)\n"
    "- **Quant.** (Quantidade de cotas/ações)"
)

# Opcional: Um expander com exemplo visual para facilitar ainda mais
with st.sidebar.expander("Ver exemplo de formato"):
  st.code("Ativo;Quant.\nPETR4;100\nVALE3;50\nHGLG11;20", language="csv")

# Único file_uploader com key única
uploaded_file = st.sidebar.file_uploader(
    "Carregue seu arquivo CSV ou Excel da carteira",
    type=["csv", "xlsx"],
    key="carteira_file_uploader",
)
importar_btn = st.sidebar.button("Importar / Processar", type="primary")

cotacao_dolar = obter_cotacao_dolar()
st.sidebar.info(f"💵 Cotação USD/BRL: **R$ {cotacao_dolar:.2f}**")

# Botão para limpar completamente a sessão e resetar a tela
if st.sidebar.button("🗑️ Limpar Carteira Salva"):
  if "df_carteira" in st.session_state:
    del st.session_state["df_carteira"]
  if os.path.exists(CACHE_FILE):
    try:
      os.remove(CACHE_FILE)
    except Exception:
      pass
  st.sidebar.warning("Sessão limpa com sucesso!")
  st.rerun()

# 4. Processamento quando o usuário envia um novo CSV via uploader
if uploaded_file is not None and importar_btn:
    try:
        # Tenta ler com separador ';' (padrão BR)
        try:
            df_raw = pd.read_csv(uploaded_file, sep=";", encoding="utf-8-sig")
            if len(df_raw.columns) <= 1:
                uploaded_file.seek(0)
                df_raw = pd.read_csv(uploaded_file, sep=",", encoding="utf-8-sig")
        except Exception:
            uploaded_file.seek(0)
            df_raw = pd.read_csv(uploaded_file, sep=",", encoding="utf-8-sig")

        # --- VALIDAÇÃO ROBUSTA DE COLUNAS ---
        df_raw.columns = df_raw.columns.str.strip().str.replace('.', '', regex=False)
        
        colunas_possiveis_ativo = ['Ativo', 'Ticker', 'Cod']
        colunas_possiveis_qtd = ['Quantidade', 'Quant', 'Qtd']
        
        tem_ativo = any(col in df_raw.columns for col in colunas_possiveis_ativo)
        tem_qtd = any(col in df_raw.columns for col in colunas_possiveis_qtd)
        
        if not tem_ativo or not tem_qtd:
            st.sidebar.error("❌ Erro: O CSV precisa conter colunas para Ativo e Quantidade (ex: Ativo, Quant).")
        elif df_raw.empty:
            st.sidebar.error("❌ Erro: O arquivo CSV enviado está vazio.")
        else:
            # Padroniza nomes internos
            renomear = {}
            for c in df_raw.columns:
                if c in colunas_possiveis_ativo: renomear[c] = 'Ativo'
                if c in colunas_possiveis_qtd: renomear[c] = 'Quantidade'
            
            df_raw = df_raw.rename(columns=renomear)
            
            # Trata valores numéricos
            df_raw['Quantidade'] = pd.to_numeric(df_raw['Quantidade'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # --- BUSCA O PREÇO ATUAL AUTOMATICAMENTE NA INTERNET ---
            st.sidebar.info("Buscando cotações atuais na B3...")
            precos = []
            for ativo in df_raw['Ativo']:
                preco = buscar_preco_atual(ativo)
                precos.append(preco)
            
            df_raw['PrecoAtual'] = precos
            df_raw['Total'] = df_raw['Quantidade'] * df_raw['PrecoAtual']

            # Salva no cache e na sessão
            os.makedirs("data", exist_ok=True)
            df_raw.to_csv(CACHE_FILE, sep=";", index=False, encoding="utf-8-sig")
            st.session_state['df_carteira'] = df_raw
            st.sidebar.success("Cotações atualizadas e dados importados com sucesso!")
            st.rerun()
            
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao processar o arquivo: {e}")
# Carrega do arquivo cache local caso exista na sessão mas não esteja carregado
if (
    "df_carteira" not in st.session_state
    and os.path.exists(CACHE_FILE)
    and os.path.getsize(CACHE_FILE) > 0
):
  try:
    st.session_state["df_carteira"] = pd.read_csv(CACHE_FILE, sep=";")
  except Exception:
    pass

# 5. Validação e Carga do DataFrame para exibição nas telas
if (
    "df_carteira" in st.session_state
    and st.session_state["df_carteira"] is not None
    and not st.session_state["df_carteira"].empty
):
  df = st.session_state["df_carteira"].copy()

  # Mapeia ou calcula a coluna numérica de saldo com base no campo 'Total' gerado pelo uploader
  if "Total" in df.columns:
      df["Saldo_Num"] = pd.to_numeric(df["Total"].astype(str).str.replace(',', '.'), errors='coerce').fillna(0.0)
  elif "Saldo_Num" in df.columns:
      pass 
  else:
      col_saldo_orig = next(
          (c for c in df.columns if "Saldo" in c or "Valor Total" in c or "Patrimônio" in c),
          None,
      )
      df["Saldo_Num"] = (
          df[col_saldo_orig].apply(parse_moeda) if col_saldo_orig else 0.0
      )

  # Verifica se existe coluna de classe de ativo, caso contrário cria uma padrão "Ações/FIIs" para não quebrar os gráficos
  col_classe = next(
      (c for c in ["Tipo de ativo", "Tipo", "Classe", "Categoria"] if c in df.columns),
      None,
  )
  if not col_classe:
      df["Tipo de Ativo"] = "Ações/FIIs"
      col_classe = "Tipo de Ativo"

  if "% Ideal_Num" not in df.columns:
      df["% Ideal_Num"] = 0.0

  patrimonio_total = df["Saldo_Num"].sum()
  if patrimonio_total > 0:
      df["% Carteira_Num"] = (df["Saldo_Num"] / patrimonio_total) * 100
  else:
      df["% Carteira_Num"] = 0.0

  # --- CARDS DE DESTAQUE ---
  st.subheader("📊 Resumo Geral")
  col1, col2, col3 = st.columns(3)

  patrimonio_fmt = (
      f"R$ {patrimonio_total:,.2f}"
      .replace(",", "X")
      .replace(".", ",")
      .replace("X", ".")
  )

  col1.metric(label="Patrimônio Total", value=patrimonio_fmt)
  col2.metric(label="Total de Posições", value=f"{len(df)} ativos")

  if col_classe and col_classe in df.columns:
      df_agrupado_classe = df.groupby(col_classe)["Saldo_Num"].sum()
      maior_classe = (
          df_agrupado_classe.idxmax()
          if not df_agrupado_classe.empty and df_agrupado_classe.sum() > 0
          else "N/A"
      )
      col3.metric(label="Maior Classe", value=str(maior_classe))
  else:
      col3.metric(label="Maior Classe", value="N/A")

  st.divider()

  # --- GRÁFICOS DO SPRINT 1 ---
  st.subheader("📈 Distribuição do Patrimônio")
  col_left, col_right = st.columns(2)

  with col_left:
      if col_classe and col_classe in df.columns and patrimonio_total > 0:
          df_classe = df.groupby(col_classe)["Saldo_Num"].sum().reset_index()
          fig_donut = px.pie(
              df_classe,
              names=col_classe,
              values="Saldo_Num",
              hole=0.45,
              title="Alocação Atual por Classe de Ativo",
              color_discrete_sequence=px.colors.qualitative.Safe,
          )
          fig_donut.update_traces(textinfo="percent+label")
          st.plotly_chart(fig_donut, use_container_width=True)
      else:
          st.info("Aguardando dados válidos para exibir o gráfico de rosca.")

  with col_right:
      if col_classe and col_classe in df.columns:
          df_comparativo = (
              df.groupby(col_classe)[["% Carteira_Num", "% Ideal_Num"]]
              .sum()
              .reset_index()
          )
          df_comparativo.columns = [col_classe, "% Carteira", "% Ideal"]

          fig_bar = px.bar(
              df_comparativo,
              x=col_classe,
              y=["% Carteira", "% Ideal"],
              barmode="group",
              title="Alocação Atual vs. Meta Ideal (%)",
              labels={
                  "value": "Percentual (%)",
                  "variable": "Legenda",
                  col_classe: "Tipo de Ativo",
              },
              color_discrete_sequence=["#1f77b4", "#aec7e8"],
          )
          st.plotly_chart(fig_bar, use_container_width=True)
      else:
          st.info("Aguardando dados válidos para exibir o gráfico de barras.")

  st.divider()

  # --- TABELA DE POSIÇÕES DETALHADAS ---
  st.subheader("📋 Posições Atuais da Carteira")

  # Remove colunas auxiliares numéricas da exibição final para o usuário
  colunas_para_remover = [
      "Saldo_Num",
      "% Carteira_Num",
      "% Ideal_Num",
      "Ideal_Num",
  ]
  df_display = df.drop(
      columns=[c for c in colunas_para_remover if c in df.columns],
      errors="ignore",
  ).copy()
  df_display = df_display.fillna("-")

  st.dataframe(df_display, use_container_width=True)

else:
  st.info(
      "👋 Nenhum dado carregado. Faça o upload do arquivo CSV na barra lateral e"
      " clique em **Importar / Processar**."
  )