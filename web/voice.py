from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import edge_tts


async def _generate_tts(text: str, output_path: str, voice: str = "es-ES-AlvaroNeural") -> str:
    communicator = edge_tts.Communicate(text=text, voice=voice)
    await communicator.save(output_path)
    return output_path


def generate_voice_file(text: str, voice: str = "es-ES-AlvaroNeural") -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""

    tmp_dir = Path(tempfile.gettempdir())
    output_path = tmp_dir / "agri_summary.mp3"
    asyncio.run(_generate_tts(cleaned, str(output_path), voice=voice))
    return str(output_path)