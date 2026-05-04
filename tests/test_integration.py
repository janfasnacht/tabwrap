# tests/test_integration.py
"""End-to-end request → compile → response coverage per format."""

import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient

from tabwrap import Format
from tabwrap.api import create_app
from tabwrap.core import TabWrap

SAMPLE_TEX = r"""
\begin{tabular}{lcr}
\toprule
Header 1 & Header 2 & Header 3 \\
\midrule
1 & 2 & 3 \\
4 & 5 & 6 \\
\bottomrule
\end{tabular}
"""


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def tex_payload():
    return ("test_table.tex", SAMPLE_TEX.encode("utf-8"), "text/plain")


def _post(client, tex_payload, **form):
    return client.post(
        "/api/compile",
        files={"file": tex_payload},
        data=form,
    )


def test_complex_table(tmp_path):
    content = r"""
    \begin{tabular}{@{}l*{3}{c}@{}}
    \toprule
    & \multicolumn{3}{c}{Treatment Effect} \\
    \cmidrule(lr){2-4}
    Outcome & (1) & (2) & (3) \\
    \midrule
    Variable 1 & 0.123*** & 0.456** & 0.789* \\
               & (0.023) & (0.045) & (0.067) \\
    Variable 2 & -0.321* & -0.654** & -0.987*** \\
               & (0.034) & (0.056) & (0.078) \\
    \midrule
    Controls & Yes & Yes & No \\
    Observations & 1000 & 1000 & 1000 \\
    R$^2$ & 0.23 & 0.34 & 0.45 \\
    \bottomrule
    \end{tabular}
    """
    tex_file = tmp_path / "complex_table.tex"
    tex_file.write_text(content)

    compiler = TabWrap()
    result = compiler.compile_tex(input_path=tex_file, output_dir=tmp_path)
    assert result.artifacts[Format.PDF].exists()
    assert (tmp_path / "complex_table_compiled.pdf").exists()


def test_request_compile_response_pdf(client, tex_payload):
    response = _post(client, tex_payload, formats="pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "test_table_compiled.pdf" in response.headers["content-disposition"]


def test_request_compile_response_png(client, tex_payload):
    response = _post(client, tex_payload, formats="png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "test_table_compiled.png" in response.headers["content-disposition"]


def test_request_compile_response_svg(client, tex_payload):
    response = _post(client, tex_payload, formats="svg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert "test_table_compiled.svg" in response.headers["content-disposition"]


def test_multi_format_returns_zip_no_manifest_by_default(client, tex_payload):
    response = _post(client, tex_payload, formats="pdf,png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "test_table_compiled.zip" in response.headers["content-disposition"]

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        names = set(zf.namelist())
    assert {"test_table_compiled.pdf", "test_table_compiled.png"} == names


def test_multi_format_with_manifest(client, tex_payload):
    response = _post(client, tex_payload, formats="pdf,png,svg", manifest="true")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        names = set(zf.namelist())
        assert "manifest.json" in names
        manifest = json.loads(zf.read("manifest.json"))

    assert {"test_table_compiled.pdf", "test_table_compiled.png", "test_table_compiled.svg"} <= names
    assert set(manifest["page_counts"].keys()) == {"pdf", "png", "svg"}
    assert "pdflatex" in manifest["timings"]
    assert isinstance(manifest["detected_packages"], list)
    assert isinstance(manifest["warnings"], list)


def test_legacy_png_alias_returns_raw_binary(client, tex_payload):
    response = _post(client, tex_payload, png="true")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_invalid_tabular_returns_400(client):
    payload = ("invalid.tex", b"not a table", "text/plain")
    response = client.post("/api/compile", files={"file": payload})
    assert response.status_code == 400


def test_unknown_format_returns_400(client, tex_payload):
    response = _post(client, tex_payload, formats="pdf,jpg")
    assert response.status_code == 400
    assert "Unknown format" in response.json()["detail"]
