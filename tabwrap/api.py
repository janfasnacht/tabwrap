# tabwrap/api.py
try:
    from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse
    from pydantic import BaseModel, Field
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
except ImportError as e:
    raise ImportError("API dependencies not installed. Install with: pip install tabwrap[api]") from e

import tempfile
from datetime import datetime
from pathlib import Path

try:
    from importlib.metadata import version as get_version

    __version__ = get_version("tabwrap")
except Exception:
    # Loud sentinel so a broken build (e.g. package metadata missing
    # from the image) is obvious in the /api/health response instead
    # of silently reporting a stale hardcoded version.
    __version__ = "unknown"

import os as _os

from .config import setup_logging
from .core import CompilerMode, TabWrap
from .exceptions import (
    ConversionError,
    DependencyError,
    InvalidLatexError,
    LatexCompilationError,
)
from .latex import is_valid_tabular_content
from .output import bundle_artifacts
from .result import resolve_formats
from .settings import Settings

_log_file = None
if not _os.getenv("TABWRAP_LOG_DIR"):  # Development mode (no systemd)
    _log_dir = Path("logs")
    _log_dir.mkdir(exist_ok=True)
    _log_file = _log_dir / f"api_{datetime.now():%Y%m%d}.log"
logger = setup_logging(module_name=__name__, log_file=_log_file)


# Pydantic Models
class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = __version__


class CompileOptions(BaseModel):
    packages: str = Field("", description="Comma-separated LaTeX packages")
    landscape: bool = Field(False, description="Use landscape orientation")
    no_rescale: bool = Field(False, description="Disable automatic table resizing")
    show_filename: bool = Field(False, description="Show filename as header")
    formats: str = Field("", description="Comma-separated formats: pdf,png,svg. Defaults to pdf.")
    png: bool = Field(False, description="Alias: include png in formats")
    svg: bool = Field(False, description="Alias: include svg in formats")
    manifest: bool = Field(False, description="Include manifest.json in multi-format zip bundle")
    parallel: bool = Field(False, description="Use parallel processing for faster compilation")
    max_workers: int = Field(None, description="Maximum number of parallel workers")


class ErrorResponse(BaseModel):
    detail: str


def create_app():
    """Create FastAPI application."""
    settings = Settings()

    limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_per_hour])

    app = FastAPI(
        title="TabWrap API",
        description="LaTeX table fragment compilation API with automatic OpenAPI documentation",
        version=__version__,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return HealthResponse()

    @app.post(
        "/api/compile",
        response_class=FileResponse,
        tags=["Compilation"],
        responses={
            200: {
                "description": "Compiled file (binary) or zip bundle when multiple formats are requested",
                "content": {
                    "application/pdf": {},
                    "image/png": {},
                    "image/svg+xml": {},
                    "application/zip": {},
                },
            },
            400: {"model": ErrorResponse, "description": "Bad Request - Invalid input"},
            429: {"model": ErrorResponse, "description": "Too Many Requests - Rate limit exceeded"},
            500: {"model": ErrorResponse, "description": "Internal Server Error - Compilation failed"},
        },
    )
    @limiter.limit(settings.rate_limit_per_minute)
    async def compile_table(
        request: Request,
        file: UploadFile = File(..., description="LaTeX table file (.tex)"),
        packages: str = Form("", description="Comma-separated LaTeX packages"),
        landscape: bool = Form(False, description="Use landscape orientation"),
        no_rescale: bool = Form(False, description="Disable automatic table resizing"),
        show_filename: bool = Form(False, description="Show filename as header"),
        formats: str = Form("", description="Comma-separated formats: pdf,png,svg. Defaults to pdf."),
        png: bool = Form(False, description="Alias: include png in formats"),
        svg: bool = Form(False, description="Alias: include svg in formats"),
        manifest: bool = Form(False, description="Include manifest.json in multi-format zip bundle"),
        parallel: bool = Form(False, description="Use parallel processing for faster compilation"),
        max_workers: int = Form(None, description="Maximum number of parallel workers (default: CPU cores)"),
    ):
        """Compile a LaTeX table fragment into one or more output formats.

        Single-format requests return the raw artifact with the matching media type.
        Multi-format requests return a zip bundle (`application/zip`); pass
        `manifest=true` to also include a `manifest.json` with page counts,
        detected packages, warnings, and timings.
        """
        try:
            if not file.filename or not file.filename.endswith(".tex"):
                raise HTTPException(status_code=400, detail="Invalid file. Only .tex files are allowed.")

            try:
                resolved_formats = resolve_formats(formats, png=png, svg=svg, strict_alias_combo=True)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

            content = await file.read()
            try:
                content_str = content.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="File must be valid UTF-8 encoded text.")

            is_valid, reason = is_valid_tabular_content(content_str)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid LaTeX content: {reason}")

            temp_dir = Path(tempfile.mkdtemp())

            try:
                input_path = temp_dir / file.filename
                with open(input_path, "w", encoding="utf-8") as f:
                    f.write(content_str)

                with TabWrap(mode=CompilerMode.WEB) as compiler:
                    try:
                        result = compiler.compile_tex(
                            input_path=input_path,
                            output_dir=temp_dir,
                            packages=packages,
                            landscape=landscape,
                            no_rescale=no_rescale,
                            show_filename=show_filename,
                            formats=resolved_formats,
                            keep_tex=False,
                            parallel=parallel,
                            max_workers=max_workers,
                        )
                    except InvalidLatexError as e:
                        raise HTTPException(status_code=400, detail=f"Invalid file content: {e}")
                    except LatexCompilationError as e:
                        raise HTTPException(status_code=400, detail=f"LaTeX compilation error: {e}")
                    except DependencyError as e:
                        raise HTTPException(status_code=500, detail=f"Missing dependency: {e}")
                    except ConversionError as e:
                        raise HTTPException(status_code=500, detail=f"Conversion error: {e}")

                stem = Path(file.filename).stem

                if len(result.artifacts) == 1:
                    only_fmt, only_path = next(iter(result.artifacts.items()))
                    filename = f"{stem}_compiled{only_fmt.extension}"
                    return FileResponse(path=str(only_path), media_type=only_fmt.media_type, filename=filename)

                manifest_payload = result.to_manifest() if manifest else None
                zip_path = bundle_artifacts(result.artifacts, temp_dir, stem, manifest=manifest_payload)
                return FileResponse(
                    path=str(zip_path),
                    media_type="application/zip",
                    filename=f"{stem}_compiled.zip",
                )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Unexpected error during compilation: {e}")
                raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"API error: {e}")
            raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

    return app


# Create app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
