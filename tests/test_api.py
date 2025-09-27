# tests/test_api.py
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from tabwrap.api import create_app


@pytest.fixture
def client():
    """Create FastAPI test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_tex():
    """Create a sample tex file content."""
    return r"""
\begin{tabular}{lcr}
\toprule
Header 1 & Header 2 & Header 3 \\
\midrule
1 & 2 & 3 \\
4 & 5 & 6 \\
\bottomrule
\end{tabular}
"""


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


def test_compile_valid_table(client, sample_tex, tmp_path):
    """Test successful compilation of a valid table."""
    # Create test file
    tex_file = tmp_path / "test_table.tex"
    tex_file.write_text(sample_tex)

    with open(tex_file, 'rb') as f:
        response = client.post(
            '/api/compile',
            files={'file': ('test_table.tex', f, 'text/plain')},
            data={
                'landscape': False,
                'png': False,
                'svg': False,
            }
        )

    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/pdf'
    assert 'test_table_compiled.pdf' in response.headers['content-disposition']


def test_compile_invalid_content(client, tmp_path):
    """Test compilation with invalid table content."""
    invalid_tex = r"This is not a valid table"
    tex_file = tmp_path / "invalid.tex"
    tex_file.write_text(invalid_tex)

    with open(tex_file, 'rb') as f:
        response = client.post(
            '/api/compile',
            files={'file': ('invalid.tex', f, 'text/plain')}
        )

    assert response.status_code == 400
    data = response.json()
    assert "Invalid LaTeX content" in data["detail"]


def test_png_output(client, sample_tex, tmp_path):
    """Test PNG output option."""
    tex_file = tmp_path / "test_table.tex"
    tex_file.write_text(sample_tex)

    with open(tex_file, 'rb') as f:
        response = client.post(
            '/api/compile',
            files={'file': ('test_table.tex', f, 'text/plain')},
            data={'png': True}
        )

    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/png'
    assert 'test_table_compiled.png' in response.headers['content-disposition']


def test_svg_output(client, sample_tex, tmp_path):
    """Test SVG output option."""
    tex_file = tmp_path / "test_table.tex"
    tex_file.write_text(sample_tex)

    with open(tex_file, 'rb') as f:
        response = client.post(
            '/api/compile',
            files={'file': ('test_table.tex', f, 'text/plain')},
            data={'svg': True}
        )

    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/svg+xml'
    assert 'test_table_compiled.svg' in response.headers['content-disposition']


def test_png_and_svg_mutually_exclusive(client, sample_tex, tmp_path):
    """Test that PNG and SVG options are mutually exclusive."""
    tex_file = tmp_path / "test_table.tex"
    tex_file.write_text(sample_tex)

    with open(tex_file, 'rb') as f:
        response = client.post(
            '/api/compile',
            files={'file': ('test_table.tex', f, 'text/plain')},
            data={'png': True, 'svg': True}
        )

    assert response.status_code == 400
    data = response.json()
    assert "Cannot specify both PNG and SVG" in data["detail"]


def test_invalid_file_type(client, tmp_path):
    """Test uploading non-.tex file."""
    invalid_file = tmp_path / "test.txt"
    invalid_file.write_text("Not a tex file")

    with open(invalid_file, 'rb') as f:
        response = client.post(
            '/api/compile',
            files={'file': ('test.txt', f, 'text/plain')}
        )

    assert response.status_code == 400
    data = response.json()
    assert "Only .tex files are allowed" in data["detail"]


def test_landscape_option(client, sample_tex, tmp_path):
    """Test landscape orientation option."""
    tex_file = tmp_path / "test_table.tex"
    tex_file.write_text(sample_tex)

    with open(tex_file, 'rb') as f:
        response = client.post(
            '/api/compile',
            files={'file': ('test_table.tex', f, 'text/plain')},
            data={'landscape': True}
        )

    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/pdf'


def test_packages_option(client, sample_tex, tmp_path):
    """Test custom packages option."""
    tex_file = tmp_path / "test_table.tex"
    tex_file.write_text(sample_tex)

    with open(tex_file, 'rb') as f:
        response = client.post(
            '/api/compile',
            files={'file': ('test_table.tex', f, 'text/plain')},
            data={'packages': 'booktabs,siunitx'}
        )

    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/pdf'