import os
import tempfile
from datetime import datetime
from pathlib import Path


def flush_report(file_path: Path, topic: str, sections: dict, status: str = "COMPLETE") -> None:
    """Write a pipeline report from collected sections, atomically.

    Creates a temp file, writes the markdown content, then atomically
    replaces the target — so the report is never left half-written
    on a crash.
    """
    lines = [f"# Pipeline Report — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    lines.append(f"## Status")
    lines.append(f"{status}")
    lines.append("")
    lines.append(f"## Topic")
    lines.append(f"{topic}")
    lines.append("")

    for label, content in sections.items():
        if content is None:
            continue
        lines.append(f"## {label}")
        lines.append("")
        lines.append(str(content))
        lines.append("")

    # Atomic write via temp file + os.replace
    tmp_dir = file_path.parent
    fd, tmp_path = tempfile.mkstemp(dir=str(tmp_dir), suffix=".tmp")
    try:
        os.write(fd, "\n".join(lines).encode())
        os.close(fd)
        os.replace(tmp_path, str(file_path))
    except Exception:
        os.close(fd)
        os.unlink(tmp_path)
        raise


def save_article(
    article_file: Path,
    text: str,
    illustration_path: Path | None = None,
) -> None:
    """Save the final article markdown, atomically."""
    lines = []
    if illustration_path:
        lines.append(f"![Illustration]({illustration_path.name})")
        lines.append("")
    lines.append(text)
    content = "\n".join(lines)

    tmp_dir = article_file.parent
    fd, tmp_path = tempfile.mkstemp(dir=str(tmp_dir), suffix=".tmp")
    try:
        os.write(fd, content.encode())
        os.close(fd)
        os.replace(tmp_path, str(article_file))
    except Exception:
        os.close(fd)
        os.unlink(tmp_path)
        raise
