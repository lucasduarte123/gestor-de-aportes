from dotenv import load_dotenv
from fastapi import FastAPI

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

from app.api.carteira_routes import router as carteira_router
from app.api.macro_routes import router as macro_router

app = FastAPI(
    title="Portfolio Dashboard & Macro Impact API",
    description="API para gestão de carteira de investimentos e análise macroeconômica via Gemini.",
    version="1.0.0"
)

app.include_router(carteira_router)
app.include_router(macro_router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "API rodando com sucesso!"}