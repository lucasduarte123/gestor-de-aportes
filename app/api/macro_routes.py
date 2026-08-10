from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.schemas.macro import AnaliseMacroSchema
from app.services.macro_service import analisar_impacto_macro

router = APIRouter(prefix="/macro", tags=["Análise Macro"])

class MacroRequest(BaseModel):
    tickers: list[str]

@router.post("/analise", response_model=AnaliseMacroSchema)
async def gerar_analise_macro(payload: MacroRequest):
    if not payload.tickers:
        raise HTTPException(status_code=400, detail="A lista de ativos (tickers) não pode estar vazia.")
    
    try:
        resultado = analisar_impacto_macro(payload.tickers)
        return resultado
    except Exception as e:
        # Exibe o erro exato retornado pela biblioteca ou API
        raise HTTPException(status_code=500, detail=str(e))