from pathlib import Path
import site

from fastapi import APIRouter, UploadFile, File, Response
from fastapi import Depends, HTTPException, status
from starlette.responses import StreamingResponse, FileResponse
from pydantic import BaseModel


from fpdf import FPDF
import markdown
import black


from utils.utils import get_admin_user
from utils.misc import calculate_sha256, get_gravatar_url

from config import OLLAMA_BASE_URLS, DATA_DIR, UPLOAD_DIR, ENABLE_ADMIN_EXPORT
from constants import ERROR_MESSAGES
from typing import List

router = APIRouter()


@router.get("/gravatar")
async def get_gravatar(
    email: str,
):
    return get_gravatar_url(email)


class CodeFormatRequest(BaseModel):
    code: str


@router.post("/code/format")
async def format_code(request: CodeFormatRequest):
    try:
        formatted_code = black.format_str(request.code, mode=black.Mode())
        return {"code": formatted_code}
    except black.NothingChanged:
        return {"code": request.code}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MarkdownForm(BaseModel):
    md: str


@router.post("/markdown")
async def get_html_from_markdown(
    form_data: MarkdownForm,
):
    return {"html": markdown.markdown(form_data.md)}


class ChatForm(BaseModel):
    title: str
    messages: List[dict]


@router.post("/pdf")
async def download_chat_as_pdf(
    form_data: ChatForm,
):
    pdf = FPDF()
    pdf.add_page()

    # When running in docker, workdir is /app/backend, so fonts is in /app/backend/static/fonts
    FONTS_DIR = Path("./static/fonts")

    # Non Docker Installation

    # When running using `pip install` the static directory is in the site packages.
    if not FONTS_DIR.exists():
        FONTS_DIR = Path(site.getsitepackages()[0]) / "static/fonts"
    # When running using `pip install -e .` the static directory is in the site packages.
    # This path only works if `open-webui serve` is run from the root of this project.
    if not FONTS_DIR.exists():
        FONTS_DIR = Path("./backend/static/fonts")

    pdf.add_font("NotoSans", "", f"{FONTS_DIR}/NotoSans-Regular.ttf")
    pdf.add_font("NotoSans", "b", f"{FONTS_DIR}/NotoSans-Bold.ttf")
    pdf.add_font("NotoSans", "i", f"{FONTS_DIR}/NotoSans-Italic.ttf")
    pdf.add_font("NotoSansKR", "", f"{FONTS_DIR}/NotoSansKR-Regular.ttf")
    pdf.add_font("NotoSansJP", "", f"{FONTS_DIR}/NotoSansJP-Regular.ttf")

    pdf.set_font("NotoSans", size=12)
    pdf.set_fallback_fonts(["NotoSansKR", "NotoSansJP"])

    pdf.set_auto_page_break(auto=True, margin=15)

    # Adjust the effective page width for multi_cell
    effective_page_width = (
        pdf.w - 2 * pdf.l_margin - 10
    )  # Subtracted an additional 10 for extra padding

    # Add chat messages
    for message in form_data.messages:
        role = message["role"]
        content = message["content"]
        pdf.set_font("NotoSans", "B", size=14)  # Bold for the role
        pdf.multi_cell(effective_page_width, 10, f"{role.upper()}", 0, "L")
        pdf.ln(1)  # Extra space between messages

        pdf.set_font("NotoSans", size=10)  # Regular for content
        pdf.multi_cell(effective_page_width, 6, content, 0, "L")
        pdf.ln(1.5)  # Extra space between messages

    # Save the pdf with name .pdf
    pdf_bytes = pdf.output()

    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment;filename=chat.pdf"},
    )


@router.get("/db/download")
async def download_db(user=Depends(get_admin_user)):
    if not ENABLE_ADMIN_EXPORT:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
    from apps.webui.internal.db import engine

    if engine.name != "sqlite":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DB_NOT_SQLITE,
        )
    return FileResponse(
        engine.url.database,
        media_type="application/octet-stream",
        filename="webui.db",
    )


@router.get("/litellm/config")
async def download_litellm_config_yaml(user=Depends(get_admin_user)):
    return FileResponse(
        f"{DATA_DIR}/litellm/config.yaml",
        media_type="application/octet-stream",
        filename="config.yaml",
    )
