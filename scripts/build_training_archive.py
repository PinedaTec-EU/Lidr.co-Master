#!/usr/bin/env python3

from __future__ import annotations

import json
import mimetypes
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_ROOT = REPO_ROOT / "training-archive" / "ai-engineering-2026-04"
STAGING_DIR = ARCHIVE_ROOT / ".staging"
MANIFEST_PATH = ARCHIVE_ROOT / "manifest.json"


@dataclass
class AssetRef:
    url: str
    alt: str = ""


@dataclass
class SnapshotRecord:
    slug: str
    source_url: str
    title: str
    archived_at: str
    discovered_links: list[dict[str, str]]
    group_hint: str | None = None
    snapshot: str | None = None
    article_html: str | None = None
    title_html: str | None = None
    imgs: list[dict[str, str]] | None = None
    iframes: list[dict[str, str]] | None = None
    text_preview: str | None = None


def clean_text(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def slugify_from_url(url: str) -> str:
    return Path(urllib.parse.urlparse(url).path).name


def parse_snapshot_record(path: Path) -> SnapshotRecord:
    payload = json.loads(path.read_text())
    return SnapshotRecord(
        slug=payload["slug"],
        source_url=payload["source_url"],
        title=payload["title"],
        archived_at=payload["archived_at"],
        discovered_links=payload.get("discovered_links", []),
        group_hint=payload.get("group_hint"),
        snapshot=payload.get("snapshot"),
        article_html=payload.get("article_html"),
        title_html=payload.get("title_html"),
        imgs=payload.get("imgs"),
        iframes=payload.get("iframes"),
        text_preview=payload.get("text_preview"),
    )


def classify_group(record: SnapshotRecord) -> str:
    if record.group_hint:
        return record.group_hint
    text = f"{record.slug} {record.title}".lower()
    session_08_markers = [
        "pgvector",
        "bbdd-vectoriales",
        "vectoriales-2026",
        "indice-vectorial",
        "diskann",
        "busqueda-semantica",
        "techo-de-pgvector",
        "contenido-y-el-ejercicio-de-este-modulo-98724293",
    ]
    session_09_markers = [
        "arquitectura-rag",
        "fundamentos-de-rag",
        "diagnostico-arquitectonico-del-sistema-rag-actual",
        "del-cag-estatico-al-flujo-rag",
        "reformulacion-de-queries",
        "retrieval-que-no-es-solo-cosine",
        "augmentation-ensamblar-contexto",
        "la-capa-de-datos-como-servicio",
        "contenido-y-el-ejercicio-de-este-modulo-98724306",
    ]
    session_10_markers = [
        "sesion-10-tecnicas-de-recuperacion",
        "tecnicas-de-recuperacion",
        "ejercicio-tecnicas-avanzadas-de-recuperacion",
        "reranking-cuando-el-top-k-vectorial-no-es-suficiente",
        "como-saber-si-el-reranking-compensa",
        "busqueda-hibrida",
        "expansion-y-descomposicion-de-consultas",
        "multi-indice-y-routing",
        "filtrado-contextual-y-temporal",
        "contenido-de-este-modulo-98724321",
    ]
    if any(marker in text for marker in session_08_markers):
        return "08-session"
    if any(marker in text for marker in session_09_markers):
        return "09-session"
    if any(marker in text for marker in session_10_markers):
        return "10-session"
    if "sesion-1" in text or "sesión 1" in text:
        return "01-session"
    if "sesion-2" in text or "sesión 2" in text:
        return "02-session"
    if "sesion-3" in text or "sesión 3" in text:
        return "03-session"
    if "sesion-4" in text or "sesión 4" in text:
        return "04-session"
    if "sesion-5" in text or "sesión 5" in text:
        return "05-session"
    if "sesion-6" in text or "sesión 6" in text:
        return "06-session"
    if "sesion-7" in text or "sesión 7" in text:
        return "07-session"
    if "sesion-8" in text or "sesión 8" in text:
        return "08-session"
    if "sesion-9" in text or "sesión 9" in text:
        return "09-session"
    if "sesion-10" in text or "sesión 10" in text:
        return "10-session"
    if "pre-curso" in text or "pre curso" in text:
        return "00-pre-course"
    if "bienvenida" in text or "plataforma" in text or "modulo-de-bienvenida" in text:
        return "00-intro"
    if "proyecto-final" in text or "proyecto final" in text:
        return "99-final-project"
    return "98-misc"


def safe_filename_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    name = Path(parsed.path).name or "asset"
    name = urllib.parse.unquote(name)
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    if not name:
        name = "asset"
    return name


def asset_extension(content_type: str | None, url: str) -> str:
    guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
    if guessed:
        return guessed
    suffix = Path(urllib.parse.urlparse(url).path).suffix
    return suffix or ".bin"


def download_asset(url: str, target_dir: Path, used_names: set[str]) -> str | None:
    if not url.startswith("http"):
        return None
    base = safe_filename_from_url(url)
    stem = Path(base).stem or "asset"
    suffix = Path(base).suffix
    if not suffix:
        suffix = asset_extension(None, url)
    candidate = f"{stem}{suffix}"
    counter = 2
    while candidate in used_names:
        candidate = f"{stem}-{counter}{suffix}"
        counter += 1
    target = target_dir / candidate
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
            content_type = response.headers.get("Content-Type")
        if not target.suffix:
            target = target.with_suffix(asset_extension(content_type, url))
        target.write_bytes(data)
        used_names.add(target.name)
        return target.name
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


class MarkdownHTMLConverter(HTMLParser):
    def __init__(self, image_map: dict[str, str], iframe_map: dict[str, str]) -> None:
        super().__init__(convert_charrefs=True)
        self.image_map = image_map
        self.iframe_map = iframe_map
        self.out: list[str] = []
        self.href_stack: list[str] = []
        self.list_stack: list[str] = []
        self.in_li = False

    def _write(self, text: str) -> None:
        self.out.append(text)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(tag[1])
            self._write("\n" + "#" * level + " ")
        elif tag == "p":
            self._write("\n\n")
        elif tag in {"strong", "b"}:
            self._write("**")
        elif tag in {"em", "i"}:
            self._write("*")
        elif tag == "br":
            self._write("\n")
        elif tag in {"ul", "ol"}:
            self.list_stack.append(tag)
            self._write("\n")
        elif tag == "li":
            bullet = "- " if not self.list_stack or self.list_stack[-1] == "ul" else "1. "
            self._write("\n" + bullet)
            self.in_li = True
        elif tag == "a":
            self.href_stack.append(attr.get("href") or "")
            self._write("[")
        elif tag == "img":
            src = attr.get("src") or ""
            alt = clean_text(attr.get("alt") or "") or "image"
            local = self.image_map.get(src, src)
            self._write(f"\n\n![{alt}](./assets/{local})\n\n" if local != src else f"\n\n![{alt}]({src})\n\n")
        elif tag == "iframe":
            src = attr.get("src") or ""
            local = self.iframe_map.get(src)
            if local:
                self._write(f"\n\n[Video offline](./assets/{local})\n\n")
            elif src:
                self._write(f"\n\n[Video]({src})\n\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._write("\n")
        elif tag == "p":
            self._write("\n")
        elif tag in {"strong", "b"}:
            self._write("**")
        elif tag in {"em", "i"}:
            self._write("*")
        elif tag in {"ul", "ol"} and self.list_stack:
            self.list_stack.pop()
            self._write("\n")
        elif tag == "li":
            self.in_li = False
        elif tag == "a":
            href = self.href_stack.pop() if self.href_stack else ""
            self._write(f"]({href})" if href else "]")

    def handle_data(self, data: str) -> None:
        text = clean_text(data)
        if text:
            self._write(text)

    def to_markdown(self) -> str:
        content = "".join(self.out)
        content = re.sub(r"\n{3,}", "\n\n", content)
        return content.strip() + "\n"


def snapshot_fallback_markdown(record: SnapshotRecord) -> str:
    if not record.snapshot:
        return ""
    lines = record.snapshot.splitlines()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        heading_match = re.match(r"- ['\"]?heading \"(.+?)\" \[level=(\d+)\]['\"]?(?::.*)?$", stripped)
        if heading_match:
            out.append(f"{'#' * int(heading_match.group(2))} {clean_text(heading_match.group(1))}")
            out.append("")
            continue
        paragraph_inline = re.match(r'- paragraph: "(.*)"$', stripped)
        if paragraph_inline:
            out.append(clean_text(paragraph_inline.group(1)))
            out.append("")
    return "\n".join(out).strip() + "\n"


def convert_html_to_markdown(html: str, image_map: dict[str, str], iframe_map: dict[str, str]) -> str:
    parser = MarkdownHTMLConverter(image_map=image_map, iframe_map=iframe_map)
    parser.feed(html)
    return parser.to_markdown()


def extract_article_post_links(html: str | None) -> list[str]:
    if not html:
        return []
    links = re.findall(r'href="(https://training\.lidr\.co/posts/[^"]+)"', html)
    deduped: list[str] = []
    seen: set[str] = set()
    for link in links:
        parsed_path = urllib.parse.urlparse(link).path.strip("/")
        if parsed_path.count("/") != 1:
            continue
        if link in seen:
            continue
        seen.add(link)
        deduped.append(link)
    return deduped


def build_manifest(records: list[SnapshotRecord]) -> dict:
    discovered_urls: dict[str, dict[str, str]] = {}
    for record in records:
        group = classify_group(record)
        discovered_urls[record.source_url] = {
            "url": record.source_url,
            "title": record.title,
            "slug": record.slug,
            "group": group,
            "status": "archived" if record.article_html else "partial",
        }
        for link_url in extract_article_post_links(record.article_html):
            discovered_urls.setdefault(
                link_url,
                {
                    "url": link_url,
                    "title": slugify_from_url(link_url),
                    "slug": slugify_from_url(link_url),
                    "group": classify_group(
                        SnapshotRecord(
                            slug=slugify_from_url(link_url),
                            source_url=link_url,
                            title=slugify_from_url(link_url),
                            archived_at="",
                            discovered_links=[],
                            group_hint=group,
                        )
                    ),
                    "status": "pending",
                },
            )

    items = sorted(discovered_urls.values(), key=lambda item: (item["group"], item["slug"]))
    summary = {
        "discovered_posts": len(items),
        "archived_posts": sum(1 for item in items if item["status"] == "archived"),
        "partial_posts": sum(1 for item in items if item["status"] == "partial"),
        "pending_posts": sum(1 for item in items if item["status"] == "pending"),
    }
    return {
        "course": "AI Engineering 2026/04",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root_dir": str(ARCHIVE_ROOT.relative_to(REPO_ROOT)),
        "summary": summary,
        "items": items,
    }


def clear_sessions_dir() -> None:
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    for child in ARCHIVE_ROOT.iterdir():
        if child.name in {".staging", "manifest.json"}:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def render_record(record: SnapshotRecord) -> None:
    group = classify_group(record)
    lesson_dir = ARCHIVE_ROOT / group / record.slug
    assets_dir = lesson_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    image_map: dict[str, str] = {}
    iframe_map: dict[str, str] = {}
    used_names: set[str] = set()

    for image in record.imgs or []:
        src = image.get("src") or ""
        if not src or src in image_map:
            continue
        saved = download_asset(src, assets_dir, used_names)
        if saved:
            image_map[src] = saved

    body = convert_html_to_markdown(record.article_html, image_map, iframe_map) if record.article_html else snapshot_fallback_markdown(record)
    frontmatter = {
        "title": record.title,
        "source_url": record.source_url,
        "archived_at": record.archived_at,
        "group": group,
    }
    index_path = lesson_dir / "index.md"
    index_path.write_text(
        "---\n"
        + "\n".join(f'{key}: "{value}"' for key, value in frontmatter.items())
        + "\n---\n\n"
        + body
    )


def main() -> int:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    clear_sessions_dir()
    records = [parse_snapshot_record(path) for path in sorted(STAGING_DIR.glob("*.json"))]
    for record in records:
        render_record(record)
    MANIFEST_PATH.write_text(json.dumps(build_manifest(records), ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
