"""Regression tests for issue #22: \\newcommand auto-injection and the --preamble escape hatch."""

import pytest

from tabwrap.core import CompilerMode, TabWrap
from tabwrap.latex import check_latex_dependencies

pytestmark = pytest.mark.skipif(not check_latex_dependencies()["pdflatex"], reason="pdflatex not available")


def _write_sym_table(path) -> None:
    body = [
        r"\begin{tabular}{lc}",
        r"\toprule",
        r"Var & Coef \\",
        r"\midrule",
        r"x & 1.23\sym{**} \\",
        r"y & 0.45\sym{*}  \\",
        r"\bottomrule",
        r"\end{tabular}",
        "",
    ]
    path.write_text("\n".join(body))


def _write_plain_table(path) -> None:
    body = [
        r"\begin{tabular}{lc}",
        r"\toprule",
        r"A & B \\",
        r"\midrule",
        r"C & D \\",
        r"\bottomrule",
        r"\end{tabular}",
        "",
    ]
    path.write_text("\n".join(body))


def test_sym_definition_auto_injected(tmp_path):
    """`\\sym{**}` content should auto-inject the \\newcommand and compile cleanly."""
    tex_file = tmp_path / "sym.tex"
    _write_sym_table(tex_file)

    result = TabWrap(mode=CompilerMode.CLI).compile_tex(tex_file, tmp_path, suffix="_out", keep_tex=True)

    compiled = (tmp_path / "sym_out.tex").read_text()
    assert r"\providecommand{\sym}" in compiled
    assert result.path.exists()


def test_user_preamble_injected_verbatim(tmp_path):
    """The --preamble string should be inserted verbatim and usable from the body."""
    tex_file = tmp_path / "with_foo.tex"
    body = [
        r"\begin{tabular}{lc}",
        r"\toprule",
        r"A & \foo \\",
        r"\bottomrule",
        r"\end{tabular}",
        "",
    ]
    tex_file.write_text("\n".join(body))

    result = TabWrap(mode=CompilerMode.CLI).compile_tex(
        tex_file,
        tmp_path,
        suffix="_out",
        preamble=r"\newcommand{\foo}{FOO}",
        keep_tex=True,
    )

    compiled = (tmp_path / "with_foo_out.tex").read_text()
    assert r"\newcommand{\foo}{FOO}" in compiled
    assert result.path.exists()


def test_preamble_absent_when_unused(tmp_path):
    """A plain table with no triggering commands and no --preamble should leave the preamble area empty."""
    tex_file = tmp_path / "plain.tex"
    _write_plain_table(tex_file)

    TabWrap(mode=CompilerMode.CLI).compile_tex(tex_file, tmp_path, suffix="_out", keep_tex=True)

    compiled = (tmp_path / "plain_out.tex").read_text()
    assert r"\newcommand" not in compiled
    assert r"\providecommand" not in compiled


def test_definitions_appear_after_packages(tmp_path):
    """Definition lines must come after \\usepackage so they can rely on package-defined commands."""
    tex_file = tmp_path / "ordered.tex"
    _write_sym_table(tex_file)

    TabWrap(mode=CompilerMode.CLI).compile_tex(tex_file, tmp_path, suffix="_out", keep_tex=True)

    compiled = (tmp_path / "ordered_out.tex").read_text()
    booktabs_idx = compiled.find(r"\usepackage{booktabs}")
    sym_idx = compiled.find(r"\providecommand{\sym}")
    assert booktabs_idx != -1 and sym_idx != -1
    assert sym_idx > booktabs_idx


def test_user_newcommand_overrides_auto_providecommand(tmp_path):
    """User --preamble `\\newcommand{\\sym}{...}` must override the auto `\\providecommand{\\sym}`.

    Auto-detected definitions use \\providecommand, and the user preamble is emitted
    before them, so a plain \\newcommand from the user wins without needing \\renewcommand.
    """
    tex_file = tmp_path / "override.tex"
    _write_sym_table(tex_file)

    result = TabWrap(mode=CompilerMode.CLI).compile_tex(
        tex_file,
        tmp_path,
        suffix="_out",
        preamble=r"\newcommand{\sym}[1]{[#1]}",
        keep_tex=True,
    )

    compiled = (tmp_path / "override_out.tex").read_text()
    user_idx = compiled.find(r"\newcommand{\sym}[1]{[#1]}")
    auto_idx = compiled.find(r"\providecommand{\sym}")
    assert user_idx != -1 and auto_idx != -1
    assert user_idx < auto_idx, "user preamble must come before auto definitions for override to work"
    assert result.path.exists()
