"""Regression tests for issue #21: standalone document class for single-table compiles."""

import logging

import fitz
import pytest

from tabwrap.core import CompilerMode, TabWrap
from tabwrap.latex import check_latex_dependencies

pytestmark = pytest.mark.skipif(not check_latex_dependencies()["pdflatex"], reason="pdflatex not available")


def _write_tabular(path, rows: int) -> None:
    body = ["\\begin{tabular}{lcc}", "\\toprule", "Var & Mean & SD \\\\", "\\midrule"]
    body += [f"Var {i} & {i*10}.{i % 10} & {i*5}.{i % 10} \\\\" for i in range(1, rows + 1)]
    body += ["\\bottomrule", "\\end{tabular}", ""]
    path.write_text("\n".join(body))


def test_compiled_tex_uses_standalone_class(tmp_path):
    """The wrapper template should emit `standalone` instead of article + geometry."""
    tex_file = tmp_path / "small.tex"
    _write_tabular(tex_file, rows=3)

    TabWrap(mode=CompilerMode.CLI).compile_tex(tex_file, tmp_path, suffix="_out", keep_tex=True)
    compiled = (tmp_path / "small_out.tex").read_text()

    assert "\\documentclass[varwidth" in compiled
    assert "{standalone}" in compiled
    assert "\\resizebox" not in compiled
    assert "geometry" not in compiled


def test_tall_table_fits_single_page(tmp_path):
    """A 30-row table used to overflow A4 onto page 2; standalone must keep it single-page."""
    tex_file = tmp_path / "tall.tex"
    _write_tabular(tex_file, rows=30)

    result = TabWrap(mode=CompilerMode.CLI).compile_tex(tex_file, tmp_path, suffix="_out")
    pdf_path = result.path

    with fitz.open(str(pdf_path)) as doc:
        assert len(doc) == 1, "tall table must compile to a single page under standalone"
        page = doc[0]
        # Page should be tightly fit, not A4 (~595x842pt). Check both dims are smaller
        # than A4 height to confirm auto-fit, and height tracks row count (>200pt).
        assert page.rect.width < 595
        assert 200 < page.rect.height < 800


def test_small_table_pdf_is_not_a4(tmp_path):
    """Small tables should produce small PDFs — no whitespace around them."""
    tex_file = tmp_path / "small.tex"
    _write_tabular(tex_file, rows=2)

    result = TabWrap(mode=CompilerMode.CLI).compile_tex(tex_file, tmp_path, suffix="_out")

    with fitz.open(str(result.path)) as doc:
        page = doc[0]
        assert page.rect.width < 400, f"expected tight fit, got width={page.rect.width}"
        assert page.rect.height < 200, f"expected tight fit, got height={page.rect.height}"


def test_deprecated_flags_are_no_ops_and_warn(tmp_path, caplog):
    """`landscape` and `no_rescale` should still accept input but log a deprecation warning."""
    tex_file = tmp_path / "small.tex"
    _write_tabular(tex_file, rows=2)

    with caplog.at_level(logging.WARNING, logger="tabwrap.core"):
        result = TabWrap(mode=CompilerMode.CLI).compile_tex(
            tex_file,
            tmp_path,
            suffix="_out",
            landscape=True,
            no_rescale=True,
        )

    assert result.path.exists()
    messages = " ".join(r.message for r in caplog.records)
    assert "landscape" in messages and "no_rescale" in messages
    assert "ignored" in messages
