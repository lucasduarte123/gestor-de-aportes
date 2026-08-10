import pandas as pd


def parse_moeda(valor) -> float:
  """Converte valores monetários/formatados em float numérico puro."""
  if pd.isna(valor) or valor == '' or valor is None:
    return 0.0
  if isinstance(valor, (int, float)):
    return float(valor)

  val_str = str(valor).strip()
  val_str = (
      val_str.replace('R$', '')
      .replace('US$', '')
      .replace('$', '')
      .replace('%', '')
      .strip()
  )

  if not val_str:
    return 0.0

  if ',' in val_str and '.' in val_str:
    if val_str.rfind(',') > val_str.rfind('.'):
      val_str = val_str.replace('.', '').replace(',', '.')
    else:
      val_str = val_str.replace(',', '')
  elif ',' in val_str:
    val_str = val_str.replace(',', '.')

  try:
    return float(val_str)
  except ValueError:
    return 0.0