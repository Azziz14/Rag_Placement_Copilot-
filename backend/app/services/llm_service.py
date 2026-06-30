import json
import logging
import requests
from typing import Optional, Dict, Any
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

class LLMService:
    def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        response_json: bool = False,
        provider: Optional[str] = None
    ) -> str:
        if not provider:
            provider = settings.LLM_PROVIDER.lower() if settings.LLM_PROVIDER else "gemini"
        else:
            provider = provider.lower()
        
        # Priority order of providers to try if failover is needed (Gemini first since it's most reliable)
        providers_order = ["gemini", "groq", "openrouter", "mistral", "deepseek"]
        
        def is_configured(p: str) -> bool:
            if p == "gemini":
                return bool(settings.GEMINI_API_KEY)
            if p == "groq":
                return bool(settings.GROQ_API_KEY)
            if p == "deepseek":
                return bool(settings.DEEPSEEK_API_KEY)
            if p == "openrouter":
                return bool(settings.OPENROUTER_API_KEY)
            if p == "mistral":
                return bool(settings.MISTRAL_API_KEY)
            return False

        # If chosen provider is not configured, pick the first configured one
        if not is_configured(provider):
            fallback_found = False
            for p in providers_order:
                if is_configured(p):
                    logger.warning(f"Chosen provider '{provider}' is not configured. Defaulting to '{p}'.")
                    provider = p
                    fallback_found = True
                    break
            if not fallback_found:
                raise RuntimeError("No LLM API keys are configured.")

        # Attempt invocation with fallback loop if the active call fails
        tried_providers = []
        current_provider = provider
        
        while current_provider:
            tried_providers.append(current_provider)
            try:
                if current_provider == "gemini":
                    return self._generate_with_gemini(prompt, temperature, max_tokens, response_json)
                elif current_provider == "groq":
                    return self._generate_openai_compatible(
                        url="https://api.groq.com/openai/v1/chat/completions",
                        api_key=settings.GROQ_API_KEY,
                        model=settings.GROQ_MODEL or "llama-3.3-70b-versatile",
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_json=response_json
                    )
                elif current_provider == "deepseek":
                    return self._generate_openai_compatible(
                        url="https://api.deepseek.com/chat/completions",
                        api_key=settings.DEEPSEEK_API_KEY,
                        model=settings.DEEPSEEK_MODEL or "deepseek-chat",
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_json=response_json
                    )
                elif current_provider == "openrouter":
                    headers = {
                        "HTTP-Referer": "https://interviewpilot.ai",
                        "X-Title": "InterviewPilot-AI"
                    }
                    return self._generate_openai_compatible(
                        url="https://openrouter.ai/api/v1/chat/completions",
                        api_key=settings.OPENROUTER_API_KEY,
                        model=settings.OPENROUTER_MODEL or "meta-llama/llama-3.3-70b-instruct",
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_json=response_json,
                        extra_headers=headers
                    )
                elif current_provider == "mistral":
                    return self._generate_openai_compatible(
                        url="https://api.mistral.ai/v1/chat/completions",
                        api_key=settings.MISTRAL_API_KEY,
                        model=settings.MISTRAL_MODEL or "open-mistral-nemo",
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_json=response_json
                    )
            except Exception as e:
                logger.warning(f"LLM Provider '{current_provider}' failed: {str(e)}.")
                # Find next configured provider not yet tried
                next_provider = None
                for p in providers_order:
                    if p not in tried_providers and is_configured(p):
                        next_provider = p
                        break
                
                if next_provider:
                    logger.info(f"Retrying failover with provider: '{next_provider}'")
                    current_provider = next_provider
                else:
                    raise RuntimeError(f"All configured LLM providers failed: {tried_providers}. Last error: {str(e)}")

    def _generate_openai_compatible(
        self,
        url: str,
        api_key: str,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
        response_json: bool,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> str:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        if extra_headers:
            headers.update(extra_headers)

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if response_json:
            payload["response_format"] = {"type": "json_object"}

        logger.info(f"Calling OpenAI-compatible endpoint ({url}) with model: {model}")
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=45.0
        )
        response.raise_for_status()
        res_data = response.json()
        return res_data["choices"][0]["message"]["content"]

    def _generate_with_gemini(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        response_json: bool = False
    ) -> str:
        model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"
        logger.info(f"Calling Gemini API with model: {model_name}")
        model = genai.GenerativeModel(model_name)
        
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "candidate_count": 1
        }
        if response_json:
            generation_config["response_mime_type"] = "application/json"
            
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(**generation_config)
        )
        return response.text

llm_service = LLMService()
