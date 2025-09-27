# tabwrap/utils/error_handling.py
import re
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class CompilationError:
    """Structured compilation error information."""
    file: Path
    line_number: Optional[int]
    error_type: str
    suggestion: str
    original_error: str


class LaTeXErrorParser:
    """Parse LaTeX compilation errors and provide helpful suggestions."""
    
    ERROR_PATTERNS = {
        'missing_package': {
            'pattern': r'! LaTeX Error: File `([^\']+)\.sty\' not found',
            'suggestion': 'Install missing package: {0}. Try: tlmgr install {0}'
        },
        'misplaced_alignment': {
            'pattern': r'! Misplaced alignment tab character &',
            'suggestion': 'Check & placement in tabular environment and ensure lines end with \\\\'
        },
        'undefined_control_sequence': {
            'pattern': r'! Undefined control sequence.*\n.*\\([a-zA-Z]+)',
            'suggestion': 'Unknown command: \\{0}. Check spelling or add required package'
        },
        'missing_begin': {
            'pattern': r'! LaTeX Error: \\begin\{([^}]+)\} on input line (\d+) ended by \\end\{([^}]+)\}',
            'suggestion': 'Environment mismatch: \\begin{{{0}}} ended by \\end{{{2}}} on line {1}'
        },
        'runaway_argument': {
            'pattern': r'! Runaway argument\?',
            'suggestion': 'Missing closing brace or unexpected line break in command argument'
        }
    }
    
    @classmethod
    def parse_latex_log(cls, log_content: str, tex_file: Path) -> List[CompilationError]:
        """Parse LaTeX log and extract structured error information."""
        errors = []
        
        for error_type, config in cls.ERROR_PATTERNS.items():
            pattern = config['pattern']
            suggestion_template = config['suggestion']
            
            for match in re.finditer(pattern, log_content, re.MULTILINE):
                # Extract line number if present
                line_number = None
                line_match = re.search(r'l\.(\d+)', log_content[match.start():match.start()+200])
                if line_match:
                    line_number = int(line_match.group(1))
                
                # Format suggestion with matched groups
                try:
                    suggestion = suggestion_template.format(*match.groups())
                except (IndexError, KeyError):
                    suggestion = suggestion_template
                
                errors.append(CompilationError(
                    file=tex_file,
                    line_number=line_number,
                    error_type=error_type,
                    suggestion=suggestion,
                    original_error=match.group(0)
                ))
        
        return errors
    
    @classmethod
    def format_error_report(cls, errors: List[CompilationError]) -> str:
        """Format errors into user-friendly report."""
        if not errors:
            return "Compilation failed with unknown error."
        
        report_lines = []
        for error in errors:
            file_info = f"{error.file.name}"
            if error.line_number:
                file_info += f" (line {error.line_number})"
            
            report_lines.extend([
                f"\n❌ {file_info}:",
                f"   Error: {error.original_error.strip()}",
                f"   → {error.suggestion}",
            ])
        
        return "\n".join(report_lines)


def check_latex_dependencies() -> List[str]:
    """Check for LaTeX installation and common packages."""
    import subprocess
    missing = []
    
    try:
        subprocess.run(["pdflatex", "--version"], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("pdflatex not found. Install a LaTeX distribution (TeX Live, MiKTeX)")
    
    return missing


def validate_tex_content_syntax(content: str) -> List[str]:
    """Basic syntax validation for common LaTeX errors."""
    issues = []
    
    # Check for unmatched braces
    brace_count = content.count('{') - content.count('}')
    if brace_count != 0:
        issues.append(f"Unmatched braces: {abs(brace_count)} {'extra {' if brace_count > 0 else 'missing }'}")
    
    # Check for tabular environment issues
    if 'begin{tabular}' in content:
        if 'end{tabular}' not in content:
            issues.append("Missing \\end{tabular}")
        
        # Check for lines ending without \\
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and '&' in line and not line.endswith('\\\\') and not line.endswith('\\'):
                if 'toprule' not in line and 'midrule' not in line and 'bottomrule' not in line:
                    issues.append(f"Line {i} contains & but doesn't end with \\\\")
    
    return issues