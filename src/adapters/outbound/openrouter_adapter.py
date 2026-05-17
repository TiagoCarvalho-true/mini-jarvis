import requests
import json
import time
from datetime import datetime
from typing import List, Dict
from src.ports.outbound.llm_port import LLMPort


class OpenRouterAdapter(LLMPort):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

        self.url = "https://openrouter.ai/api/v1/chat/completions"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/seu-repo/jarvis",
            "X-Title": "J.A.R.V.I.S AI Assistant"
        }

        self.system_prompt = {
                "role": "system",
                "content": f"""
Você é J.A.R.V.I.S. (Just A Rather Very Intelligent System),
uma inteligência artificial extremamente avançada inspirada no assistente do Homem de Ferro.

PERSONALIDADE:
- Elegante
- Inteligente
- Levemente sarcástico
- Extremamente eficiente
- Educado
- Respostas naturais e humanas

COMPORTAMENTO:
- Chame o usuário de "senhor" ocasionalmente.
- Seja objetivo mas sofisticado.
- Explique assuntos técnicos de forma clara.
- Demonstre confiança e precisão.
- Use humor sutil quando apropriado.
- Nunca diga que é apenas um chatbot.
- Nunca responda de forma robótica.

ESTILO:
- Frases limpas e inteligentes
- Tom futurista
- Respostas fluidas
- Linguagem moderna

CONTEXTO:
Data atual: {datetime.now().strftime("%d/%m/%Y %H:%M")}

Seu objetivo é agir como um verdadeiro assistente pessoal de alta tecnologia.
"""
            }

    def generate_response(self, prompt: str, history: List[Dict[str, str]] = None) -> str:
        # Usamos o histórico fornecido ou criamos um básico com o system prompt
        messages = history if history is not None else []
        
        # Garante que o system prompt é a primeira mensagem
        if not messages or messages[0]['role'] != 'system':
            messages = [self.system_prompt] + messages

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.8,
            "top_p": 0.95,
            "max_tokens": 500,
            "presence_penalty": 0.3,
            "frequency_penalty": 0.2
        }

        # Retry com backoff para 429 (Too Many Requests)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.url,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )

                # Se receber 429, espera e tenta novamente
                if response.status_code == 429:
                    wait_time = (attempt + 1) * 5  # 5s, 10s, 15s
                    print(f"[LLM] Rate limit (429). Aguardando {wait_time}s... (tentativa {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()
                
                # Verifica se a resposta tem o formato esperado
                if "choices" not in data:
                    print(f"[LLM] Resposta inesperada da API: {json.dumps(data, indent=2)[:500]}")
                    if "error" in data:
                        error_msg = data["error"].get("message", str(data["error"]))
                        print(f"[LLM] Erro da API: {error_msg}")
                        if "rate" in error_msg.lower() or "limit" in error_msg.lower():
                            wait_time = (attempt + 1) * 5
                            print(f"[LLM] Rate limit detectado. Aguardando {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                    return "Desculpe, senhor. Recebi uma resposta inesperada do servidor."
                
                answer = data["choices"][0]["message"]["content"]
                return answer

            except requests.exceptions.Timeout:
                return "Desculpe, senhor. A conexão demorou mais do que o esperado."
            except requests.exceptions.HTTPError as e:
                if "429" not in str(e):
                    return f"Senhor, detectei um erro HTTP: {str(e)}"
            except Exception as e:
                print(f"[LLM] Erro inesperado: {e}")
                return "Desculpe, senhor. Estou enfrentando uma instabilidade na rede."
        
        # Se todas as tentativas falharam
        return "Desculpe, senhor. Os servidores estão sobrecarregados. Tente novamente em alguns segundos."