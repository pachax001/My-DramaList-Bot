"""Utilities for fitting HTML captions within Telegram's media limits."""

from html import unescape
from html.parser import HTMLParser
import re


TELEGRAM_MEDIA_CAPTION_MAX_LENGTH = 1024
_ELLIPSIS = "…"
_TRAILING_LINK_RE = re.compile(
    r"(?P<prefix>.*?)(?P<separator>\s*)(?P<link><a\b[^>]*>.*?</a>)\s*$",
    flags=re.IGNORECASE | re.DOTALL,
)
_VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


def _utf16_length(value: str) -> int:
    """Return Telegram's string length (UTF-16 code units)."""
    return sum(2 if ord(character) > 0xFFFF else 1 for character in value)


def _prefix_by_utf16_length(value: str, max_length: int) -> str:
    """Return the longest prefix that fits in ``max_length`` UTF-16 units."""
    used = 0
    end = 0
    for end, character in enumerate(value, start=1):
        character_length = 2 if ord(character) > 0xFFFF else 1
        if used + character_length > max_length:
            return value[: end - 1]
        used += character_length
    return value[:end]


class _HTMLTextLengthParser(HTMLParser):
    """Measure rendered HTML text without counting markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.length = 0

    def handle_data(self, data: str) -> None:
        self.length += _utf16_length(data)

    def handle_entityref(self, name: str) -> None:
        self.length += _utf16_length(unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        self.length += _utf16_length(unescape(f"&#{name};"))


def html_text_length(value: str) -> int:
    """Return the UTF-16 length of the text represented by an HTML string."""
    parser = _HTMLTextLengthParser()
    parser.feed(value)
    parser.close()
    return parser.length


class _HTMLTruncator(HTMLParser):
    """Truncate rendered HTML text and close any tags left open."""

    def __init__(self, text_limit: int) -> None:
        super().__init__(convert_charrefs=False)
        self.text_limit = max(text_limit, 0)
        self.text_length = 0
        self.output: list[str] = []
        self.open_tags: list[str] = []
        self.truncated = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.truncated:
            return
        self.output.append(self.get_starttag_text())
        if tag not in _VOID_ELEMENTS:
            self.open_tags.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self.truncated:
            self.output.append(self.get_starttag_text())

    def handle_endtag(self, tag: str) -> None:
        if self.truncated:
            return
        self.output.append(f"</{tag}>")
        if self.open_tags and self.open_tags[-1] == tag:
            self.open_tags.pop()

    def handle_data(self, data: str) -> None:
        if self.truncated:
            return

        remaining = self.text_limit - self.text_length
        if _utf16_length(data) <= remaining:
            self.output.append(data)
            self.text_length += _utf16_length(data)
            return

        prefix = _prefix_by_utf16_length(data, remaining).rstrip()
        self.output.append(prefix)
        self.text_length += _utf16_length(prefix)
        self.truncated = True

    def handle_entityref(self, name: str) -> None:
        self._handle_reference(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self._handle_reference(f"&#{name};")

    def _handle_reference(self, reference: str) -> None:
        if self.truncated:
            return

        reference_length = _utf16_length(unescape(reference))
        if self.text_length + reference_length <= self.text_limit:
            self.output.append(reference)
            self.text_length += reference_length
        else:
            self.truncated = True

    def result(self) -> str:
        return "".join(self.output) + _ELLIPSIS + "".join(
            f"</{tag}>" for tag in reversed(self.open_tags)
        )


def _truncate_html(value: str, max_length: int) -> str:
    if html_text_length(value) <= max_length:
        return value

    truncator = _HTMLTruncator(max_length - _utf16_length(_ELLIPSIS))
    truncator.feed(value)
    truncator.close()
    return truncator.result()


def trim_media_caption(
    caption: str,
    max_length: int = TELEGRAM_MEDIA_CAPTION_MAX_LENGTH,
) -> str:
    """Fit an HTML caption within Telegram's limit, preserving a final link."""
    if html_text_length(caption) <= max_length:
        return caption

    match = _TRAILING_LINK_RE.fullmatch(caption)
    if match:
        link = match.group("link")
        separator = "\n" if match.group("separator") else ""
        reserved_length = html_text_length(separator + link)
        if reserved_length < max_length:
            prefix = _truncate_html(
                match.group("prefix").rstrip(),
                max_length - reserved_length,
            )
            return prefix + separator + link

    return _truncate_html(caption, max_length)
