from langchain_openai import ChatOpenAI

from app.config import get_settings


def create_chat_model(role: str = "worker") -> ChatOpenAI:
    settings = get_settings()

    if settings.model_vendor == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when MODEL_VENDOR=openai")
        model_name = settings.openai_model
        api_key = settings.openai_api_key
        base_url = None
    elif settings.model_vendor == "volcengine":
        if not settings.volcengine_api_key:
            raise ValueError("VOLCENGINE_API_KEY is required when MODEL_VENDOR=volcengine")
        model_name = settings.volcengine_model
        api_key = settings.volcengine_api_key
        base_url = settings.volcengine_base_url
    else:
        if not settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is required when MODEL_VENDOR=openrouter")
        model_name = settings.openrouter_model
        api_key = settings.openrouter_api_key
        base_url = settings.openrouter_base_url

    temperature = settings.worker_temperature
    if role == "planner":
        temperature = settings.planner_temperature
    elif role == "synthesizer":
        temperature = settings.synthesizer_temperature

    kwargs = {
        "model": model_name,
        "api_key": api_key,
        "temperature": temperature,
        "max_tokens": 1200,
        "request_timeout": 20,
        "max_retries": 1,
    }
    if base_url:
        kwargs["base_url"] = base_url

    return ChatOpenAI(**kwargs)
