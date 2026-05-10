import requests
import json
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

        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload,
                timeout=60
            )

            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            return answer

        except requests.exceptions.Timeout:
            return "Desculpe, senhor. A conexão com os servidores demorou mais do que o esperado."
        except requests.exceptions.HTTPError as e:
            return f"Senhor, detectei um erro HTTP: {str(e)}"
        except Exception as e:
            print(f"[OpenRouter Error] {e}")
            return "Desculpe, senhor. Estou enfrentando uma instabilidade na rede principal."