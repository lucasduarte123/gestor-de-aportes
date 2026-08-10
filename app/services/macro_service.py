import os
from google import genai
from google.genai import types
from app.schemas.macro import AnaliseMacroSchema

def analisar_impacto_macro(tickers: list[str]) -> AnaliseMacroSchema:
    # Lê a chave no momento exato em que a requisição chega
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente GEMINI_API_KEY não foi encontrada. Verifique seu arquivo .env.")

    # Cria o cliente com a chave dinâmica passada de forma explícita
    client = genai.Client(api_key=api_key)
    lista_ativos_str = ", ".join(tickers)
    
    prompt = f"""
    Você é um analista macroeconômico e estrategista de investimentos sênior.
    Analise o cenário econômico recente focado nos seguintes ativos:
    {lista_ativos_str}
    
    Avalie o sentimento geral do mercado para essa carteira, o nível de volatilidade/risco e faça um resumo
    executivo dos impactos e setores mais afetados.
    """

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=AnaliseMacroSchema,
        temperature=0.2,
    )

    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
        config=config,
    )
    
    return response.parsed