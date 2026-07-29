import os
import io
import re
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO

def categorizar_ativo_dinamico(linha):
    """
    Categoriza automaticamente qualquer ativo (existente ou novo)
    baseando-se no Ticker e na descrição trazida do HTML.
    """
    # Converte toda a linha da tabela para texto simples para busca ampla
    texto_linha = " ".join([str(v) for v in linha.values if pd.notna(v)]).upper()
    
    # Extrai o primeiro código/ticker em maiúsculas (ex: PETR4, MXRF11, AAPL, BTC)
    match_ticker = re.search(r'\b[A-Z0-9]{2,10}\b', texto_linha)
    ticker = match_ticker.group(0) if match_ticker else ""
    
    # 1. Renda Fixa / Tesouro Direto
    padrões_rf = [r'TESOURO', r'CDB', r'LCI', r'LCA', r'RDB', r'DEB[ÊE]NTURE', r'\bLF\b', r'CRI\b', r'CRA\b']
    if any(re.search(p, texto_linha) for p in padrões_rf):
        return "Tesouro Direto / Renda Fixa"
        
    # 2. Criptomoedas
    criptos_comuns = ['BTC', 'ETH', 'SOL', 'USDT', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT', 'LINK', 'POL', 'MATIC', 'LTC']
    if any(c in texto_linha for c in criptos_comuns) or 'CRIPTO' in texto_linha:
        return "Criptomoedas"
        
    # 3. BDRs (Ações/ETFs Internacionais negociadas na B3) -> ex: AAPL34, NVDC34
    if re.search(r'^[A-Z]{4}(34|35)$', ticker):
        return "BDRs"

    # 4. FIIs (Fundos Imobiliários)
    if 'FII' in texto_linha or 'FUNDO IMOBILI' in texto_linha or re.search(r'^[A-Z]{4}11$', ticker):
        # Se for terminado em 11 e tiver palavras de fundo, é FII
        if 'FUNDO' in texto_linha or 'IMOBIL' in texto_linha or 'FII' in texto_linha:
            return "FIIs"

    # 5. Ações Brasileiras (B3) -> Tickers terminados em 3, 4, 5, 6, 11 (ex: PETR4, VALE3, TAEE11)
    if re.search(r'^[A-Z]{4}(3|4|5|6|11)$', ticker):
        return "Ações"

    # 6. Stocks e ETFs Internacionais (EUA / Exterior) -> 1 a 5 letras sem números (ex: GOOGL, NVDA, VOO)
    if re.search(r'^[A-Z]{1,5}$', ticker):
        return "Stocks / Internacional"

    return "Outros"

# Busca o arquivo HTML salvo do Investidor10 na pasta
html_file = None
for f in os.listdir("."):
    if "Investidor10" in f and (f.endswith(".html") or f.endswith(".htm") or not "." in f):
        if not f.endswith(".csv") and not os.path.isdir(f):
            html_file = f
            break

if html_file:
    print(f"📂 Lendo arquivo: {html_file}")
    with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    
    tables = soup.find_all("table")
    all_dfs = []
    
    for table in tables:
        try:
            # io.StringIO() previne o FutureWarning no Pandas
            dfs = pd.read_html(io.StringIO(str(table)))
            if dfs:
                df = dfs[0]
                cols = [str(c).lower() for c in df.columns]
                
                # Ignora a tabela de Evolução de Patrimônio
                if any("período" in c or "ganho de capital" in c for c in cols):
                    continue
                
                # Aceita tabelas que possuem colunas de posições/ativos
                if any(term in "".join(cols) for term in ["ativo", "quant", "preço", "saldo"]):
                    all_dfs.append(df)
        except Exception:
            continue

    if all_dfs:
        consolidated = pd.concat(all_dfs, ignore_index=True)
        consolidated.drop_duplicates(inplace=True)
        
        # Categorização dinâmica aplicada em cada linha individualmente
        consolidated["Tipo de ativo"] = consolidated.apply(categorizar_ativo_dinamico, axis=1)
        
        # Reorganiza para 'Tipo de ativo' ser a 1ª coluna
        cols = ["Tipo de ativo"] + [c for c in consolidated.columns if c != "Tipo de ativo"]
        consolidated = consolidated[cols]
        
        output_file = "carteira_atual.csv"
        consolidated.to_csv(output_file, index=False, sep=";", encoding="utf-8-sig")
        print(f"🚀 Sucesso! {len(consolidated)} ativos salvos e categorizados automaticamente em '{output_file}'!")
    else:
        print("❌ Nenhuma tabela de ativos válida foi encontrada.")
else:
    print("❌ Arquivo HTML do Investidor10 não foi encontrado na pasta.")