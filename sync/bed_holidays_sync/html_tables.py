"""Extract the text of HTML tables and headed sections with the standard library parser."""

from __future__ import annotations

import html.parser
import re


class _TableParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.captions: list[str] = []
        self._caption_stack: list[list[str]] = []
        self._in_caption = False
        self._stack: list[list[list[str]]] = []
        self._cell: list[str] | None = None
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._skip += 1
        elif tag == "table":
            self._stack.append([])
            self._caption_stack.append([])
        elif tag == "caption" and self._stack:
            self._in_caption = True
        elif tag == "tr" and self._stack:
            self._stack[-1].append([])
        elif tag in ("td", "th") and self._stack:
            if not self._stack[-1]:
                self._stack[-1].append([])
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._skip = max(0, self._skip - 1)
        elif tag in ("td", "th") and self._cell is not None and self._stack:
            self._stack[-1][-1].append(normalize_space("".join(self._cell)))
            self._cell = None
        elif tag == "caption":
            self._in_caption = False
        elif tag == "table" and self._stack:
            self.tables.append([row for row in self._stack.pop() if row])
            self.captions.append(normalize_space("".join(self._caption_stack.pop())))

    def handle_data(self, data: str) -> None:
        if self._skip == 0 and self._cell is not None:
            self._cell.append(data)
        elif self._skip == 0 and self._in_caption and self._caption_stack:
            self._caption_stack[-1].append(data)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def tables(document: str) -> list[list[list[str]]]:
    """Every table in the order its end tag appears, as rows of cell texts."""
    return [rows for _, rows in captioned_tables(document)]


def captioned_tables(document: str) -> list[tuple[str, list[list[str]]]]:
    """Every table with its caption text (empty when it has none)."""
    parser = _TableParser()
    parser.feed(document)
    parser.close()
    return list(zip(parser.captions, parser.tables))
