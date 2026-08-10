import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.carteira import AtivoPosicao, ResumoCarteira
from app.services.market import buscar_preco_atual, obter_cotacao_dolar

router = APIRouter(prefix='/carteira', tags=['Carteira'])


@router.post('/upload-csv', response_model=ResumoCarteira)
async def upload_carteira_csv(file: UploadFile = File(...)):
  if not file.filename.endswith(('.csv', '.xlsx')):
    raise HTTPException(
        status_code=400, detail='O arquivo deve ser no formato CSV ou Excel.'
    )

  try:
    try:
      df_raw = pd.read_csv(file.file, sep=';', encoding='utf-8-sig')
      if len(df_raw.columns) <= 1:
        file.file.seek(0)
        df_raw = pd.read_csv(file.file, sep=',', encoding='utf-8-sig')
    except Exception:
      file.file.seek(0)
      df_raw = pd.read_csv(file.file, sep=',', encoding='utf-8-sig')

    df_raw.columns = df_raw.columns.str.strip().str.replace(
        '.', '', regex=False
    )

    colunas_possiveis_ativo = ['Ativo', 'Ticker', 'Cod']
    colunas_possiveis_qtd = ['Quantidade', 'Quant', 'Qtd']

    col_ativo = next(
        (c for c in colunas_possiveis_ativo if c in df_raw.columns), None
    )
    col_qtd = next(
        (c for c in colunas_possiveis_qtd if c in df_raw.columns), None
    )

    if not col_ativo or not col_qtd:
      raise HTTPException(
          status_code=400,
          detail=(
              'O CSV precisa conter colunas para Ativo e Quantidade (ex:'
              ' Ativo, Quant).'
          ),
      )

    posicoes = []
    patrimonio_total = 0.0

    for _, row in df_raw.iterrows():
      ticker = str(row[col_ativo]).strip().upper()
      qtd = float(str(row[col_qtd]).replace(',', '.'))
      preco = buscar_preco_atual(ticker)
      total = qtd * preco
      patrimonio_total += total

      posicoes.append(
          AtivoPosicao(
              ativo=ticker, quantidade=qtd, preco_atual=preco, total=total
          )
      )

    dolar = obter_cotacao_dolar()

    return ResumoCarteira(
        patrimonio_total=patrimonio_total,
        total_posicoes=len(posicoes),
        cotacao_dolar=dolar,
        posicoes=posicoes,
    )

  except Exception as e:
    raise HTTPException(
        status_code=500, detail=f'Erro ao processar arquivo: {str(e)}'
    )