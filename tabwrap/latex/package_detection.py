"""LaTeX package detection based on content analysis.

This module provides automatic detection of required LaTeX packages by analyzing
table content for specific commands, environments, and column types.
"""

import re


class PackageRule:
    """Represents a package detection rule."""

    def __init__(
        self,
        package: str | None = None,
        patterns: list[str] | None = None,
        regex: re.Pattern | None = None,
        definition: str | None = None,
    ):
        """
        Initialize a detection rule.

        At least one of `package` / `definition` must be set: a rule may inject a
        `\\usepackage{...}` line, a verbatim preamble line (typically a
        `\\newcommand`), or both.

        Args:
            package: LaTeX package name (e.g., "siunitx").
            patterns: List of literal strings to search for (e.g., ["\\num", "\\SI"]).
            regex: Compiled regex pattern for more complex detection.
            definition: Verbatim preamble line for commands that need a
                `\\newcommand` rather than a package (e.g., esttab's `\\sym`).
        """
        if package is None and definition is None:
            raise ValueError("PackageRule requires at least one of `package` or `definition`")
        self.package = package
        self.patterns = patterns or []
        self.regex = regex
        self.definition = definition

    def matches(self, content: str) -> bool:
        """
        Check if this rule matches the given content.

        Args:
            content: LaTeX content to analyze

        Returns:
            True if package is needed, False otherwise
        """
        # Check literal patterns first (faster)
        if self.patterns and any(pattern in content for pattern in self.patterns):
            return True

        # Check regex pattern if provided
        if self.regex and self.regex.search(content):
            return True

        return False


# Define package detection rules
PACKAGE_RULES = [
    # Table-related packages
    PackageRule("booktabs", patterns=["\\toprule", "\\midrule", "\\cmidrule", "\\bottomrule"]),
    PackageRule("tabularx", patterns=["\\tabularx", "\\begin{tabularx}"]),
    PackageRule("longtable", patterns=["\\longtable", "\\begin{longtable}"]),
    PackageRule(
        "threeparttable",
        patterns=["\\threeparttable", "\\begin{threeparttable}", "\\tablenotes", "\\begin{tablenotes}"],
    ),
    PackageRule("multirow", patterns=["\\multirow"]),
    PackageRule("multicol", patterns=["\\multicolumn"]),
    PackageRule("makecell", patterns=["\\makecell", "\\thead", "\\rothead"]),
    # Math and symbols - siunitx with both literal patterns and regex for S columns
    PackageRule(
        "siunitx",
        # Patterns: \SI and \num commands, \sisetup config, S[ for S columns with options
        patterns=["\\SI", "\\num", "\\sisetup", "S["],
        # Regex to detect S column type in tabular column specifications
        # Matches patterns like: {lScr}, {SSS}, {S}, {lSc}, etc.
        # This catches cases where S appears between other column types without brackets
        # S[ is already caught by patterns above
        regex=re.compile(r"{[lcrpX|@*\s]*S[lcrpSX|@*\s]*}"),
    ),
    PackageRule("amssymb", patterns=["\\checkmark"]),
    PackageRule("amsfonts", patterns=["\\mathbb"]),
    PackageRule("amsmath", patterns=["\\boldsymbol"]),
    # bbm for proper blackboard bold numerals (indicator functions)
    PackageRule("bbm", patterns=["\\mathbbm"]),
    # Graphics and color
    PackageRule("graphicx", patterns=["\\includegraphics"]),
    PackageRule("xcolor", patterns=["\\textcolor", "\\color"]),
    # Caption formatting
    PackageRule("caption", patterns=["\\caption*", "\\captionof"]),
    # Special characters and fonts
    PackageRule("url", patterns=["\\url"]),
    # esttab (Stata) emits \sym{**} for significance stars. Use \providecommand
    # so we silently no-op if the user has their own \sym (e.g., from a
    # copy-pasted preamble or via --preamble); pattern is \sym{ — the open
    # brace — to avoid matching the kernel command \symbol.
    PackageRule(
        patterns=[r"\sym{"],
        definition=r"\providecommand{\sym}[1]{\ifmmode^{#1}\else\textsuperscript{#1}\fi}",
    ),
]


def detect_packages(tex_content: str) -> set[str]:
    """
    Detect required LaTeX packages based on content analysis.

    Uses both literal string matching and regex patterns to identify commands,
    environments, and column types that require specific packages.

    Args:
        tex_content: The LaTeX content to analyze

    Returns:
        Set of LaTeX package commands (e.g., {"\\usepackage{booktabs}", ...})

    Examples:
        >>> content = r"\\begin{tabular}{lSS} \\toprule"
        >>> packages = detect_packages(content)
        >>> "\\usepackage{siunitx}" in packages
        True
        >>> "\\usepackage{booktabs}" in packages
        True
    """
    packages = set()

    for rule in PACKAGE_RULES:
        if rule.package is not None and rule.matches(tex_content):
            packages.add(f"\\usepackage{{{rule.package}}}")

    return packages


def detect_definitions(tex_content: str) -> list[str]:
    """
    Detect required preamble definitions (e.g., `\\newcommand` lines) based on content.

    Mirrors :func:`detect_packages` but for rules carrying a `definition` rather
    than (or in addition to) a package. Returns a sorted list for deterministic
    ordering in the generated preamble.
    """
    return sorted({rule.definition for rule in PACKAGE_RULES if rule.definition is not None and rule.matches(tex_content)})
