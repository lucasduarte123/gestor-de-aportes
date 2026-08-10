from pydantic import BaseModel, field_serializer


class AtivoBase(BaseModel):
  ativo: str
  quantidade: float


class AtivoPosicao(BaseModel):
  ativo: str
  quantidade: float
  preco_atual: float
  total: float

@field_serializer('quantidade', 'preco_atual', 'total')
def round_floats(self, val:float, _info) -> float:
  return round(val,2)

class ResumoCarteira(BaseModel):
  patrimonio_total: float
  total_posicoes: int
  cotacao_dolar: float
  posicoes: list[AtivoPosicao]

  @field_serializer('patrimonio_total', 'cotacao_dolar')
  def round_floats(self, val: float, _info) -> float:
    return round(val,2)