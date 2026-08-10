# 📊 Portfolio Dashboard API

API em FastAPI para gestão de carteira de investimentos e análise de impacto macroeconômico utilizando IA Generativa (Google Gemini API).

---

## 📌 Status do Projeto & Roadmap

### 🟢 O que já foi feito
- **Estrutura Base do Projeto:** Configuração da aplicação FastAPI com arquitetura modular em `/app/api`, `/app/schemas` e `/app/services`.
- **Upload e Processamento de Carteira:** Rota `/carteira/upload-csv` para parsing e estruturação dos dados dos ativos.
- **Integração com Gemini API (`google-genai` v2):**
  - Implementação do serviço `macro_service.py` consumindo o modelo `gemini-2.0-flash` com saída estruturada em JSON (`AnaliseMacroSchema`).
  - Tratamento de exceções e mecanismo de *fallback* resiliente para contornar limites de cota/rate-limit (`429 RESOURCE_EXHAUSTED` / `limit: 0`).
- **Documentação da API:** Mapeamento e testes interativos via Swagger UI (`http://127.0.0.1:8000/docs`).

---

### 📍 Onde paramos
A rota `POST /macro/analise` está completamente funcional, validando tickers enviados, comunicando com a API do Gemini e retornando sentimentos de mercado, volatilidade e setores afetados (com suporte a dados mockados de contingência caso a cota da chave expire).

---

### 🚀 Próximos Passos
1. **Ativação/Liberação da Cota do Gemini:**
   - Configurar faturamento no Google Cloud Console ou renovar chave de API para consumo 100% em tempo real.
2. **Dados de Mercado em Tempo Real (`market.py`):**
   - Integração com `yfinance` ou API equivalente para cotação atualizada dos ativos.
3. **Métricas da Carteira:**
   - Cálculo automático de alocação percentual por setor, rentabilidade e risco consolidado.
4. **Interface Visual (Frontend / Dashboard):**
   - Conexão do backend FastAPI com painel visual (ex: Streamlit ou React/Next.js).