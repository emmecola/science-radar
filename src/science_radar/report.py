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


def impact_totals(impacts: list[dict]) -> dict[str, float]:
    return {
        k: sum(i["value"].get(k, 0) for i in impacts)
        for k in ("energy_kwh", "carbon_g_co2", "water_liters")
    }


def impact_markdown(impacts: list[dict]) -> str:
    cols = ["step", "timestamp", "energy_kwh", "carbon_g_co2", "water_liters", "renewable_percent", "pue", "provider_id", "location"]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for entry in impacts:
        v = entry["value"]
        row = [
            entry.get("step", ""),
            entry["timestamp"],
            f"{v.get('energy_kwh', 0):.6f}",
            f"{v.get('carbon_g_co2', 0):.4f}",
            f"{v.get('water_liters', 0):.6f}",
            f"{v.get('renewable_percent', 0)}",
            f"{v.get('pue', 0)}",
            str(v.get("provider_id", "")),
            str(v.get("location", "")),
        ]
        lines.append("| " + " | ".join(row) + " |")
    totals = impact_totals(impacts)
    lines.append("")
    lines.append(
        f"**Totals** — {len(impacts)} calls · "
        f"{totals['energy_kwh']:.4f} kWh · "
        f"{totals['carbon_g_co2']:.2f} g CO2 · "
        f"{totals['water_liters']:.4f} L water"
    )
    return "\n".join(lines)
