import asyncio
from openai import AsyncOpenAI
import google.generativeai as genai
from bot.config import OPENAI_API_KEY, GEMINI_API_KEY, DEEPSEEK_API_KEY, OPENROUTER_API_KEY

# Инициализация клиентов
groq_client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.groq.com/openai/v1"
) if OPENAI_API_KEY else None

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None

deepseek_client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
) if DEEPSEEK_API_KEY else None

openrouter_client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
) if OPENROUTER_API_KEY else None

AI_MODELS = {
    "groq": {
        "name": "🚀 Groq",
        "client": groq_client,
        "model": "llama-3.3-70b-versatile",
        "available": bool(groq_client)
    },
    "gemini": {
        "name": "⭐ Gemini",
        "client": gemini_model,
        "model": None,
        "available": bool(gemini_model)
    },
    "deepseek": {
        "name": "🔍 DeepSeek",
        "client": deepseek_client,
        "model": "deepseek-chat",
        "available": bool(deepseek_client)
    },
    "openrouter": {
        "name": "🌐 OpenRouter",
        "client": openrouter_client,
        "model": "openai/gpt-4o-mini",
        "available": bool(openrouter_client)
    }
}

async def ask_ai(ai_name: str, prompt: str, system_prompt: str = "Ты юридический помощник. Отвечай на русском языке четко и по делу."):
    """Запрос к выбранному AI"""
    
    if ai_name not in AI_MODELS:
        return None, f"❌ AI {ai_name} не найден"
    
    model = AI_MODELS[ai_name]
    if not model["available"]:
        return None, f"❌ {model['name']} временно недоступен"
    
    try:
        if ai_name == "gemini":
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model["client"].generate_content(f"{system_prompt}\n\nВопрос: {prompt}")
            )
            return response.text, None
        
        elif ai_name in ["groq", "deepseek", "openrouter"]:
            response = await model["client"].chat.completions.create(
                model=model["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            return response.choices[0].message.content, None
        
    except Exception as e:
        return None, f"❌ Ошибка: {str(e)[:200]}"
    
    return None, "❌ Неизвестная ошибка"