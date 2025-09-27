# tabwrap/api.py
try:
    from fastapi import FastAPI, File, Form, HTTPException, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse
    from pydantic import BaseModel, Field
except ImportError as e:
    raise ImportError("API dependencies not installed. Install with: pip install tabwrap[api]") from e

import tempfile
from datetime import datetime
from pathlib import Path

from .config import setup_logging
from .core import CompilerMode, TabWrap
from .latex import FileValidationError, is_valid_tabular_content

logger = setup_logging(module_name=__name__, log_file=Path("logs") / f"api_{datetime.now():%Y%m%d}.log")


# Pydantic Models
class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"


class CompileOptions(BaseModel):
    packages: str = Field("", description="Comma-separated LaTeX packages")
    landscape: bool = Field(False, description="Use landscape orientation")
    no_rescale: bool = Field(False, description="Disable automatic table resizing")
    show_filename: bool = Field(False, description="Show filename as header")
    png: bool = Field(False, description="Output PNG instead of PDF")
    svg: bool = Field(False, description="Output SVG instead of PDF")
    parallel: bool = Field(False, description="Use parallel processing for faster compilation")
    max_workers: int = Field(None, description="Maximum number of parallel workers")


class ErrorResponse(BaseModel):
    detail: str


def create_app():
    """Create FastAPI application."""
    app = FastAPI(
        title="TabWrap API",
        description="LaTeX table fragment compilation API with automatic OpenAPI documentation",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
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
            200: {"description": "Compiled file", "content": {"application/pdf": {}, "image/png": {}, "image/svg+xml": {}}},
            400: {"model": ErrorResponse, "description": "Bad Request - Invalid input"},
            500: {"model": ErrorResponse, "description": "Internal Server Error - Compilation failed"},
        },
    )
    async def compile_table(
        file: UploadFile = File(..., description="LaTeX table file (.tex)"),
        packages: str = Form("", description="Comma-separated LaTeX packages"),
        landscape: bool = Form(False, description="Use landscape orientation"),
        no_rescale: bool = Form(False, description="Disable automatic table resizing"),
        show_filename: bool = Form(False, description="Show filename as header"),
        png: bool = Form(False, description="Output PNG instead of PDF"),
        svg: bool = Form(False, description="Output SVG instead of PDF"),
        parallel: bool = Form(False, description="Use parallel processing for faster compilation"),
        max_workers: int = Form(None, description="Maximum number of parallel workers (default: CPU cores)"),
    ):
        """
        Compile LaTeX table fragment to PDF, PNG, or SVG.

        Upload a .tex file containing a LaTeX table fragment (like \\begin{tabular}...\\end{tabular})
        and get back a compiled PDF, PNG, or SVG file.

        The system automatically detects required LaTeX packages and handles compilation.
        """
        try:
            # Validate file type
            if not file.filename or not file.filename.endswith(".tex"):
                raise HTTPException(status_code=400, detail="Invalid file. Only .tex files are allowed.")

            # Validate mutually exclusive options
            if png and svg:
                raise HTTPException(status_code=400, detail="Cannot specify both PNG and SVG output formats.")

            # Read file content
            content = await file.read()
            try:
                content_str = content.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="File must be valid UTF-8 encoded text.")

            # Validate LaTeX content
            if not is_valid_tabular_content(content_str):
                raise HTTPException(status_code=400, detail="Invalid LaTeX content. Must contain tabular environment.")

            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp())

            try:
                # Save uploaded file
                input_path = temp_dir / file.filename
                with open(input_path, "w", encoding="utf-8") as f:
                    f.write(content_str)

                # Compile with TabWrap
                with TabWrap(mode=CompilerMode.WEB) as compiler:
                    try:
                        output_path = compiler.compile_tex(
                            input_path=input_path,
                            output_dir=temp_dir,
                            packages=packages,
                            landscape=landscape,
                            no_rescale=no_rescale,
                            show_filename=show_filename,
                            png=png,
                            svg=svg,
                            keep_tex=False,
                            parallel=parallel,
                            max_workers=max_workers,
                        )
                    except FileValidationError as e:
                        raise HTTPException(status_code=400, detail=f"Invalid file content: {str(e)}")
                    except RuntimeError as e:
                        # Check if it's a validation error
                        error_msg = str(e)
                        if any(phrase in error_msg for phrase in ["Invalid tabular content", "No tabular environment found"]):
                            raise HTTPException(status_code=400, detail=f"Invalid LaTeX content: {error_msg}")
                        else:
                            raise HTTPException(status_code=500, detail=f"Compilation failed: {error_msg}")

                # Determine content type and filename
                stem = Path(file.filename).stem
                if svg:
                    media_type = "image/svg+xml"
                    filename = f"{stem}_compiled.svg"
                elif png:
                    media_type = "image/png"
                    filename = f"{stem}_compiled.png"
                else:
                    media_type = "application/pdf"
                    filename = f"{stem}_compiled.pdf"

                # Return file
                return FileResponse(path=str(output_path), media_type=media_type, filename=filename)

            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except Exception as e:
                logger.error(f"Unexpected error during compilation: {e}")
                raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
            finally:
                # Cleanup is handled by TabWrap context manager
                pass

        except HTTPException:
            # Re-raise HTTP exceptions as-is
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
