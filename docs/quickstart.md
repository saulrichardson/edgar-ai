# Quick-start

1. **Clone & install**

   ```bash
   git clone https://github.com/your-org/edgar-ai.git
   cd edgar-ai
   pip install -e ".[test]"   # creates an editable install and pulls deps
   ```

2. **Set your OpenAI key** (or a gateway-compatible provider)

   ```bash
   export EDGAR_AI_OPENAI_API_KEY="sk-…"
   ```

3. **Run the extraction pipeline** on a single exhibit

   ```bash
   python -m edgar_ai.cli extract path/to/10-K/EX-10.1.htm
   ```

   You should see JSON rows streaming to stdout.

4. **Inspect LLM traffic (optional)**

   ```bash
   python -m edgar_ai.cli extract --record-llm …
   jq . ~/.cache/edgar-ai/llm-traffic/requests/*.json | less
   ```

5. **Bring up the Gateway in Docker** (replaces direct OpenAI calls)

   ```bash
   docker compose up -d llm-gateway
   export EDGAR_AI_LLM_GATEWAY_URL=http://localhost:9000/v1/chat/completions
   ```

   The pipeline will now hit your local proxy; traffic is cheaper to inspect
   and you can mock responses during offline development.

That’s it – dig deeper via [`development.md`](development.md) or open the code.

