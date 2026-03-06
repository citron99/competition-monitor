from datetime import datetime
import uuid

from fastapi import APIRouter

from backend.config import settings
from backend.services.parserservice import parser_service
from backend.services.openaiservice import openai_service
from backend.models.schemas import (
    ParseDemoResponse,
    ParsedContent,
    HistoryItem,
    HistoryResponse,
)

router = APIRouter()

# Простая in-memory история
HISTORY: list[HistoryItem] = []


@router.post("/parsedemo", response_model=ParseDemoResponse)
async def parsedemo():
    """
    Демонстрационный эндпоинт:
    1) Парсит сайт конкурента через Selenium (ParserService)
    2) Анализирует текст (title + h1 + первый абзац)
    3) Анализирует скриншот через Vision (analyze_image)
    4) Сохраняет краткое резюме в историю
    """
    # Берём первый URL из настроек (можно сделать по запросу)
    url = settings.competitor_urls[0] if settings.competitor_urls else "https://example.com"

    # 1. Парсинг страницы и получение скриншота
    title, h1, first_paragraph, screenshot_bytes, error = await parser_service.parse_url(url)

    if error:
        parsed = ParsedContent(
            url=url,
            title=None,
            h1=None,
            first_paragraph=None,
            analysis=None,
            error=error,
        )
        return ParseDemoResponse(success=False, data=parsed, error=error)

    # 2. Анализ текста (title + h1 + первый абзац)
    text_analysis = await openai_service.analyze_parsed_content(
        title=title,
        h1=h1,
        paragraph=first_paragraph,
    )

    # 3. Анализ изображения (скриншот) — опционально, если скрин есть
    image_analysis_summary = ""
    if screenshot_bytes:
        screenshot_b64 = parser_service.screenshot_to_base64(screenshot_bytes)
        image_analysis = await openai_service.analyze_image(
            image_base64=screenshot_b64,
            mime_type="image/png",
        )

        # Краткое резюме по изображению для истории
        image_analysis_summary = (
            f"Визуальный стиль: {image_analysis.visual_style_score}/10, "
            f"design_score: {image_analysis.design_score}/10, "
            f"animation_potential: {image_analysis.animation_potential}/10"
        )

    # 4. Формируем ParsedContent для ответа
    parsed = ParsedContent(
        url=url,
        title=title,
        h1=h1,
        first_paragraph=first_paragraph,
        analysis=text_analysis,
        error=None,
    )

    # 5. Сохраняем в историю: текстовое резюме + коротко по картинке
    HISTORY.append(
        HistoryItem(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            request_type="parse",
            request_summary=f"Парсинг {url}",
            response_summary=(
                (text_analysis.summary[:150] if text_analysis and text_analysis.summary else "")
                + (" | " + image_analysis_summary if image_analysis_summary else "")
            ),
        )
    )

    return ParseDemoResponse(success=True, data=parsed, error=None)


@router.get("/history", response_model=HistoryResponse)
async def history():
    """
    Возвращает in-memory историю запросов.
    """
    return HistoryResponse(
        items=HISTORY,
        total=len(HISTORY),
    )
