"""
Скрипт запуска приложения Мониторинг конкурентов
"""
import uvicorn
import logging

from backend.config import settings, logger  # logger инициализируется в config


# Настраиваем уровень логирования для нашего логгера
logging.getLogger("competitor_monitor").setLevel(logging.INFO)


if __name__ == "__main__":
    host_to_show = "localhost" if settings.api_host in ("0.0.0.0", "127.0.0.1") else settings.api_host

    print()
    print("=" * 60)
    print("🚀 МОНИТОРИНГ КОНКУРЕНТОВ - AI Ассистент")
    print("=" * 60)
    print()
    print(f"📍 Веб-интерфейс:  http://{host_to_show}:{settings.api_port}")
    print(f"📚 Документация:  http://{host_to_show}:{settings.api_port}/docs")
    print(f"📖 ReDoc:         http://{host_to_show}:{settings.api_port}/redoc")
    print()
    print(f"🤖 Модель текста: {settings.openai_model}")
    print(f"👁️ Модель vision: {settings.openai_vision_model}")
    print(f"🔑 API ключ:      {'✓ Настроен' if settings.proxy_api_key else '✗ НЕ ЗАДАН!'}")
    print()
    print("-" * 60)
    print("Логи запросов будут отображаться ниже...")
    print("-" * 60)
    print()

    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info",
    )
