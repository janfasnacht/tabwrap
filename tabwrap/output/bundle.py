"""Bundle multiple compile artifacts into a single ZIP for multi-format responses."""

import json
import zipfile
from pathlib import Path

from ..result import Format


def bundle_artifacts(
    artifacts: dict[Format, Path],
    output_dir: Path,
    stem: str,
    *,
    suffix: str = "_compiled",
    manifest: dict | None = None,
) -> Path:
    """Write a ZIP containing all artifacts (and an optional manifest.json).

    The ZIP itself is named ``{stem}{suffix}.zip``. Each artifact is stored
    under its own filename (``path.name``) so any custom suffix the caller
    passed to the compile pipeline is preserved verbatim. When ``manifest``
    is provided it is JSON-serialised and added as ``manifest.json``.
    """
    zip_path = output_dir / f"{stem}{suffix}.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in artifacts.values():
            zf.write(path, arcname=path.name)

        if manifest is not None:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2, default=str))

    return zip_path
