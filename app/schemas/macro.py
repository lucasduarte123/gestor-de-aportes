from typing import Literal
from pydantic import BaseModel, Field


class AnaliseMacroSchema(BaseModel):
  sentimento: Literal['Altista', 'Neutro', 'Baixista'] = Field(
      description='Sentimento geral do mercado para a carteira.'
  )
  nivel_risco: Literal['Alto', 'Médio', 'Baixo'] = Field(
      description='Nível de volatilidade/risco estimado.'
  )
  resumo_impacto: str = Field(
      description=(
          'Resumo executivo de como os eventos macro impactam os setores da'
          ' carteira.'
      )
  )
  setores_afetados: list[str] = Field(
      description='Principais setores citados na análise.'
  )