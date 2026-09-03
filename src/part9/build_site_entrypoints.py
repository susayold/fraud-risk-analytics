from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def build_root_entrypoint() -> None:
    source = (ROOT / "part-9.html").read_text(encoding="utf-8")
    root_html = source.replace(
        '<link rel="canonical" href="https://susayold.github.io/fraud-risk-analytics/part-9.html">',
        '<link rel="canonical" href="https://susayold.github.io/fraud-risk-analytics/">',
    )
    (ROOT / "index.html").write_text(root_html, encoding="utf-8")


if __name__ == "__main__":
    build_root_entrypoint()
    print("Root entrypoint synced to Part 9")
