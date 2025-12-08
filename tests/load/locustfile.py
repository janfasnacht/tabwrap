"""
Locust load testing for TabWrap API.

This load test simulates realistic usage patterns:
- ~10 requests/minute per user (matching rate limits)
- Mix of simple and complex table compilations
- Validates capacity for production deployment

Run with:
    locust -f tests/load/locustfile.py --host=https://api.tabwrap.janfasnacht.com --users 10 --spawn-rate 1 --run-time 10m
"""

import random

from locust import HttpUser, between, task

# Test LaTeX table fragments
SIMPLE_TABLE = r"""\begin{tabular}{ll}
A & B \\
C & D \\
\end{tabular}"""

MEDIUM_TABLE = r"""
\begin{tabular}{lrrr}
\toprule
Variable & Mean & SD & N \\
\midrule
Treatment & 12.5 & 3.2 & 100 \\
Control & 10.3 & 2.8 & 100 \\
\bottomrule
\end{tabular}
"""

COMPLEX_TABLE = r"""
\begin{tabular}{p{3cm}*{5}{r}}
\toprule
\multicolumn{1}{c}{Category} & Q1 & Q2 & Q3 & Q4 & Total \\
\midrule
Revenue (\$M) & 125.3 & 138.7 & 152.1 & 168.9 & 585.0 \\
Expenses (\$M) & 98.2 & 105.6 & 112.3 & 119.8 & 435.9 \\
Profit (\$M) & 27.1 & 33.1 & 39.8 & 49.1 & 149.1 \\
\midrule
Margin (\%) & 21.7 & 23.9 & 26.2 & 29.1 & 25.5 \\
\bottomrule
\end{tabular}
"""


class TabWrapUser(HttpUser):
    """
    Simulated user making compilation requests to TabWrap API.

    Wait time is 5-6 seconds between requests, yielding ~10 requests/minute,
    which matches the production rate limit.
    """

    wait_time = between(5, 6)

    def on_start(self):
        """Called when a user starts."""
        # Check API health on startup
        self.client.get("/api/health")

    @task(10)
    def compile_simple_table(self):
        """Compile a simple 2x2 table (most common use case)."""
        files = {"file": ("test_simple.tex", SIMPLE_TABLE, "text/plain")}
        with self.client.post("/api/compile", files=files, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                # Rate limit hit - expected behavior, mark as success
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(5)
    def compile_medium_table(self):
        """Compile a medium statistics table with booktabs."""
        files = {"file": ("test_medium.tex", MEDIUM_TABLE, "text/plain")}
        data = {"packages": "booktabs"}
        with self.client.post("/api/compile", files=files, data=data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def compile_complex_table(self):
        """Compile a complex multi-column table."""
        files = {"file": ("test_complex.tex", COMPLEX_TABLE, "text/plain")}
        data = {"packages": "booktabs,multirow", "landscape": random.choice(["true", "false"])}
        with self.client.post("/api/compile", files=files, data=data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def compile_png_output(self):
        """Compile table as PNG (less common)."""
        files = {"file": ("test_png.tex", SIMPLE_TABLE, "text/plain")}
        data = {"png": "true"}
        with self.client.post("/api/compile", files=files, data=data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def health_check(self):
        """Periodic health check."""
        self.client.get("/api/health")
