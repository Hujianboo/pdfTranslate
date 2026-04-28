from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str


def render_markdown(source_name: str | Path, pages: Iterable[ExtractedPage]) -> str:
    source_title = Path(source_name).name
    sections = [f"# {source_title}"]

    for page in pages:
        sections.append(f"## Page {page.page_number}")
        if page.text:
            sections.append(page.text)

    return "\n\n".join(sections).rstrip() + "\n"
