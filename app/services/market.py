import requests
import yfinance as yf


def buscar_preco_atual(ticker: str) -> float:
  """Busca o preço atual do ativo na B3 via yfinance."""
  try:
    simbolo = ticker.strip().upper()
    if not simbolo.endswith('.SA') and len(simbolo) > 4:
      simbolo_b3 = simbolo + '.SA'
    else:
      simbolo_b3 = simbolo

    dados = yf.Ticker(simbolo_b3)
    hist = dados.history(period='1d')

    if not hist.empty:
      return float(hist['Close'].iloc[-1])

    if simbolo_b3 != simbolo:
      hist_alt = yf.Ticker(simbolo).history(period='1d')
      if not hist_alt.empty:
        return float(hist_alt['Close'].iloc[-1])

    return 0.0
  except Exception:
    return 0.0


def obter_cotacao_dolar() -> float:
  """Busca a cotação atual do Dólar em tempo real usando a AwesomeAPI."""
  try:
    response = requests.get(
        'https://economia.awesomeapi.com.br/json/last/USD-BRL', timeout=5
    )
    data = response.json()
    return float(data['USDBRL']['bid'])
  except Exception:
    return 5.20