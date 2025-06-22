# tests/test_api.py
import pytest
from pathlib import Path
from tex_compiler.api import create_app


@pytest.fixture
def app():
    """Create test app instance."""
    app = create_app({
        'TESTING': True,
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024
    })
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


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
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'


def test_compile_valid_table(client, sample_tex, tmp_path):
    """Test successful compilation of a valid table."""
    # Create test file
    tex_file = tmp_path / "test_table.tex"
    tex_file.write_text(sample_tex)

    with open(tex_file, 'rb') as f:
        response = client.post(
            '/api/compile',
            data={
                'file': (f, 'test_table.tex'),
                'landscape': 'false',
                'png': 'false'
            },
            content_type='multipart/form-data'
        )

    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'
    assert 'test_table_compiled.pdf' in response.headers['Content-Disposition']


def test_compile_invalid_content(client, tmp_path):
    """Test compilation with invalid table content."""
    invalid_tex = r"This is not a valid table"
    tex_file = tmp_path / "invalid.tex"
    tex_file.write_text(invalid_tex)

    with open(tex_file, 'rb') as f:
        response = client.post(
            '/api/compile',
            data={
                'file': (f, 'invalid.tex')
            },
            content_type='multipart/form-data'
        )

    assert response.status_code == 400
    assert 'Invalid table content' in response.json['error']


def test_png_output(client, sample_tex, tmp_path):
    """Test PNG output option."""
    tex_file = tmp_path / "test_table.tex"
    tex_file.write_text(sample_tex)

    with open(tex_file, 'rb') as f:
        response = client.post(
            '/api/compile',
            data={
                'file': (f, 'test_table.tex'),
                'png': 'true'
            },
            content_type='multipart/form-data'
        )

    # Add these debug lines
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        data = response.get_json()
        print(f"Error message: {data.get('error', 'No error message')}")

        # Check if PDF exists in temp directory
        temp_dir = Path('/var/folders/tz/yckbhlqd58122jdxxjpf4d400000gp/T/tex_compiler_pxue11af')
        if temp_dir.exists():
            print("Files in temp directory:")
            for file in temp_dir.glob('*'):
                print(f"- {file.name} ({file.stat().st_size} bytes)")

    assert response.status_code == 200