#!/usr/bin/env python3
"""
TabWrap API Smoke Tests

Post-deployment validation script to verify core functionality.
Tests health endpoint, successful compilation, and error handling.

Usage:
    ./scripts/smoke_test.py [BASE_URL]
    ./scripts/smoke_test.py https://api.tabwrap.janfasnacht.com
    ./scripts/smoke_test.py http://localhost:8000  # default
"""

import sys

import requests


def test_health_check(base_url: str) -> None:
    """Test 1: Health check endpoint."""
    print("Test 1: Health check endpoint...")
    r = requests.get(f"{base_url}/api/health", timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"

    data = r.json()
    assert data["status"] == "healthy", f"Expected 'healthy', got {data['status']}"
    assert "version" in data, "Missing version field"

    print(f"  ✓ API is healthy (version: {data['version']})")


def test_successful_compilation(base_url: str) -> None:
    """Test 2: Successful PDF compilation."""
    print("Test 2: Successful PDF compilation...")

    latex_content = r"""\begin{tabular}{ll}
A & B \\
C & D \\
\end{tabular}"""
    files = {"file": ("test.tex", latex_content, "text/plain")}

    r = requests.post(f"{base_url}/api/compile", files=files, timeout=30)

    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.headers["content-type"] == "application/pdf", f"Expected PDF, got {r.headers['content-type']}"

    # Verify it's a valid PDF (starts with %PDF)
    assert r.content.startswith(b"%PDF"), "Response is not a valid PDF file"

    print(f"  ✓ Compilation successful ({len(r.content)} bytes)")


def test_png_compilation(base_url: str) -> None:
    """Test 3: PNG output format."""
    print("Test 3: PNG output format...")

    latex_content = r"""\begin{tabular}{ll}
X & Y \\
Z & W \\
\end{tabular}"""
    files = {"file": ("test_png.tex", latex_content, "text/plain")}
    data = {"png": "true"}

    r = requests.post(f"{base_url}/api/compile", files=files, data=data, timeout=30)

    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.headers["content-type"] == "image/png", f"Expected PNG, got {r.headers['content-type']}"

    # Verify it's a valid PNG (magic bytes)
    assert r.content.startswith(b"\x89PNG"), "Response is not a valid PNG file"

    print(f"  ✓ PNG compilation successful ({len(r.content)} bytes)")


def test_invalid_content(base_url: str) -> None:
    """Test 4: Invalid LaTeX content (should return 400)."""
    print("Test 4: Invalid LaTeX content handling...")

    invalid_content = "This is not valid LaTeX table content"
    files = {"file": ("bad.tex", invalid_content, "text/plain")}

    r = requests.post(f"{base_url}/api/compile", files=files, timeout=10)

    assert r.status_code == 400, f"Expected 400 for invalid content, got {r.status_code}"

    data = r.json()
    assert "detail" in data, "Missing error detail"
    assert "tabular" in data["detail"].lower(), "Error message should mention tabular environment"

    print("  ✓ Invalid content rejected correctly")


def test_package_support(base_url: str) -> None:
    """Test 5: LaTeX package support (booktabs)."""
    print("Test 5: LaTeX package support...")

    latex_content = r"""
\begin{tabular}{lr}
\toprule
Variable & Value \\
\midrule
Treatment & 12.5 \\
Control & 10.3 \\
\bottomrule
\end{tabular}
"""
    files = {"file": ("booktabs_test.tex", latex_content, "text/plain")}
    data = {"packages": "booktabs"}

    r = requests.post(f"{base_url}/api/compile", files=files, data=data, timeout=30)

    assert r.status_code == 200, f"Expected 200 with booktabs, got {r.status_code}"
    assert r.content.startswith(b"%PDF"), "Response is not a valid PDF"

    print("  ✓ Package support working (booktabs)")


def test_landscape_orientation(base_url: str) -> None:
    """Test 6: Landscape orientation."""
    print("Test 6: Landscape orientation...")

    latex_content = r"""\begin{tabular}{llll}
A & B & C & D \\
\end{tabular}"""
    files = {"file": ("landscape.tex", latex_content, "text/plain")}
    data = {"landscape": "true"}

    r = requests.post(f"{base_url}/api/compile", files=files, data=data, timeout=30)

    assert r.status_code == 200, f"Expected 200 with landscape, got {r.status_code}"

    print("  ✓ Landscape orientation working")


def main(base_url: str = "http://localhost:8000") -> None:
    """Run all smoke tests."""
    print(f"\n{'=' * 60}")
    print("TabWrap API Smoke Tests")
    print(f"Target: {base_url}")
    print(f"{'=' * 60}\n")

    tests = [
        test_health_check,
        test_successful_compilation,
        test_png_compilation,
        test_invalid_content,
        test_package_support,
        test_landscape_orientation,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test(base_url)
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except requests.RequestException as e:
            print(f"  ✗ REQUEST FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ UNEXPECTED ERROR: {e}")
            failed += 1
        print()

    print(f"{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}\n")

    if failed > 0:
        print("❌ Smoke tests FAILED")
        sys.exit(1)
    else:
        print("✅ All smoke tests PASSED")
        sys.exit(0)


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    main(url)
