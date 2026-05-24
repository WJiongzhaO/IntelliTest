"""FR 6.0 — 输出与导出 API。"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.engines.export_service.exporter import (
    ExportArtifact,
    ExportFormat,
    export_artifact,
)

router = APIRouter(prefix="/export", tags=["Output Export"])


@router.post("/artifact")
async def export_artifact_endpoint(
    artifact: ExportArtifact,
    file_format: ExportFormat = Query(default="xlsx", alias="format"),
):
    """导出测试工件。

    前端会把已审查的需求、覆盖项和测试用例打包传入；后端负责生成标准格式文件。
    这种设计保证人工修改后的内容会被导出，而不是重新读取未审查的旧结果。
    """

    result = export_artifact(artifact, file_format)
    headers = {"Content-Disposition": f'attachment; filename="{result.filename}"'}
    return StreamingResponse(
        iter([result.content]),
        media_type=result.media_type,
        headers=headers,
    )
