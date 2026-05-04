"""Unit coverage for tabwrap.result."""

import pytest

from tabwrap import CompileResult, Format, parse_formats


def test_format_round_trip():
    assert Format("pdf") is Format.PDF
    assert Format.PNG.value == "png"
    assert Format.PNG.extension == ".png"
    assert Format.PDF.media_type == "application/pdf"
    assert Format.PNG.media_type == "image/png"
    assert Format.SVG.media_type == "image/svg+xml"


def test_parse_formats_from_string():
    assert parse_formats("pdf,png") == {Format.PDF, Format.PNG}
    assert parse_formats(" pdf , svg ") == {Format.PDF, Format.SVG}
    assert parse_formats("") == set()
    assert parse_formats(None) == set()


def test_parse_formats_from_iterable():
    assert parse_formats(["pdf", Format.PNG]) == {Format.PDF, Format.PNG}
    assert parse_formats({Format.SVG}) == {Format.SVG}


def test_parse_formats_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown format"):
        parse_formats("pdf,jpg")


def test_compile_result_default_factories_isolated():
    a = CompileResult()
    b = CompileResult()
    a.detected_packages.append("booktabs")
    a.warnings.append("Overfull")
    a.timings["pdflatex"] = 0.5
    a.page_counts[Format.PDF] = 2
    a.artifacts[Format.PDF] = "/tmp/x.pdf"  # type: ignore[assignment]

    assert b.detected_packages == []
    assert b.warnings == []
    assert b.timings == {}
    assert b.page_counts == {}
    assert b.artifacts == {}
