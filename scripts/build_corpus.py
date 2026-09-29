"""
Build the searchable corpus for any exhibit.

    python scripts/build_corpus.py --persona van-gogh
    python scripts/build_corpus.py --all
    python scripts/build_corpus.py --persona t-rex --offline   # rebuild from saved downloads

It reads the "sources" list in personas/<id>/persona.json, downloads each source, cleans it, splits it into passages of about 250 tokens (around 190 words) with a one-sentence overlap, and writes:

    personas/<id>/chunks.jsonl        one passage per line, with its source, licence and whether it is the exhibit's own words (own_words)
    personas/<id>/corpus_stats.json   size of each source, for the weekly report
    personas/<id>/sources/            raw downloads and a manifest (not committed)

Supported source types: gutenberg, wikipedia, artic (Art Institute of Chicago), met (The Metropolitan Museum of Art), smithsonian (Smithsonian Open Access).
Adding an exhibit only needs a new persona.json. This script does not change.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import date
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config

CHUNK_WORDS = 190
MAX_OVERLAP_WORDS = 60
USER_AGENT = "Echoes.ai course project (University of Maryland, DATA/MSML 641)"
TODAY = date.today().isoformat()

SKIP_WIKI_SECTIONS = {
    "see also", "references", "notes", "sources", "further reading", "external links",
    "citations", "bibliography", "footnotes", "works cited", "general and cited sources",
}

SESSION = requests.Session()

def get(url, params=None, headers=None, tries=3):
    headers = {"User-Agent": USER_AGENT, **(headers or {})}
    for attempt in range(tries):
        try:
            response = SESSION.get(url, params=params, headers=headers, timeout=60)
            if response.status_code in (429, 503) and attempt < tries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            return response
        except requests.RequestException:
            if attempt == tries - 1:
                raise
            time.sleep(3)
    return response

class _TextExtractor(HTMLParser):
    BLOCK_TAGS = {"p", "br", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "blockquote", "pre"}

    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n\n")

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)

def html_to_text(html):
    parser = _TextExtractor()
    parser.feed(html)
    return unescape("".join(parser.parts))

def fetch_gutenberg(source):
    book = source["id"]
    candidates = [
        (f"https://www.gutenberg.org/cache/epub/{book}/pg{book}.txt", False),
        (f"https://www.gutenberg.org/ebooks/{book}.txt.utf-8", False),
        (f"https://www.gutenberg.org/cache/epub/{book}/pg{book}-images.html", True),
        (f"https://www.gutenberg.org/ebooks/{book}.html.images", True),
    ]
    for url, is_html in candidates:
        response = get(url)
        if response.status_code != 200:
            continue
        response.encoding = "utf-8"
        text = html_to_text(response.text) if is_html else response.text
        if "START OF TH" in text.upper() and len(text) > 20000:
            if is_html:
                print(f"    plain text not available for #{book}, used the HTML edition")
            return strip_gutenberg(text), url
    raise RuntimeError(f"Could not download Project Gutenberg book #{book}")

def gutenberg_parts(text, source):
    """
    Split a book into the parts listed in persona.json.

    Each part starts at a heading line. Text before the first heading (title page, table of contents) is dropped, and parts marked "skip" are left out.
    Parts marked "own_words" are the exhibit's own writing and may be quoted.
    Headings are searched in order, so a heading repeated in the table of contents is not mistaken for the real one.
    """
    parts = source.get("parts")
    if not parts:
        return [(source["title"], text, None, bool(source.get("own_words", False)))]
    lines = text.splitlines()
    starts, position = [], 0
    for part in parts:
        index = next((i for i in range(position, len(lines)) if lines[i].strip() == part["heading"]), None)
        if index is None:
            raise RuntimeError(f"Heading {part['heading']!r} not found in Gutenberg book #{source['id']}")
        starts.append((index, part))
        position = index + 1
    sections = []
    for n, (index, part) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        if part.get("skip"):
            continue
        body = "\n".join(lines[index + 1:end])
        sections.append((part["label"], body, None, bool(part.get("own_words", False))))
    return sections

def strip_gutenberg(text):
    """Remove the Project Gutenberg licence header and footer."""
    start = re.search(r"\*\*\*\s*START OF TH(E|IS) PROJECT GUTENBERG EBOOK[^*]*\*\*\*", text, re.I)
    if start:
        text = text[start.end():]
    end = re.search(r"\*\*\*\s*END OF TH(E|IS) PROJECT GUTENBERG EBOOK", text, re.I)
    if end:
        text = text[:end.start()]
    text = re.sub(r"\[(Illustration|Transcriber)[^\]]*\]", " ", text, flags=re.I)
    return text

def fetch_wikipedia(source):
    api = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query", "prop": "extracts|revisions", "explaintext": 1,
        "rvprop": "ids|timestamp", "titles": source["title"], "format": "json",
        "formatversion": 2, "redirects": 1,
    }
    page = get(api, params=params).json()["query"]["pages"][0]
    if "missing" in page:
        raise RuntimeError(f"Wikipedia has no article called {source['title']!r}")
    revision = page["revisions"][0]["revid"]
    url = f"https://en.wikipedia.org/w/index.php?title={page['title'].replace(' ', '_')}&oldid={revision}"
    return page["extract"], url, revision

def wikipedia_sections(extract):
    """Split a plain-text Wikipedia extract into (section, text), dropping reference sections."""
    sections = []
    current, lines, skipping = "Introduction", [], False
    for line in extract.splitlines():
        heading = re.match(r"^(=+)\s*(.+?)\s*=+\s*$", line)
        if heading:
            if lines and not skipping:
                sections.append((current, "\n".join(lines)))
            level, name = len(heading.group(1)), heading.group(2)
            if level == 2:
                skipping = name.lower() in SKIP_WIKI_SECTIONS
            current, lines = name, []
            continue
        lines.append(line)
    if lines and not skipping:
        sections.append((current, "\n".join(lines)))
    return sections

def fetch_artic(source):
    artworks = []
    for page in range(1, 4):
        response = get(
            "https://api.artic.edu/api/v1/artworks/search",
            params={
                "q": source["query"], "limit": 100, "page": page,
                "fields": "id,title,artist_title,date_display,medium_display,description,place_of_origin",
            },
            headers={"AIC-User-Agent": USER_AGENT},
        )
        if response.status_code != 200:
            break
        try:
            payload = response.json()
        except Exception:
            break
        found = [a for a in payload.get("data", []) if a.get("artist_title") == source["artist"]]
        if not found:
            break
        artworks.extend(found)
    records = []
    for art in artworks:
        description = " ".join(html_to_text(art.get("description") or "").split())
        if not description:
            continue
        heading = f"{art['title']} ({art.get('date_display', '')})"
        text = f"{heading}. {art.get('medium_display') or ''}. {description}".replace(" .", "")
        records.append({
            "section": art["title"],
            "text": text,
            "url": f"https://www.artic.edu/artworks/{art['id']}",
        })
    return records, artworks

def fetch_met(source):
    base = "https://collectionapi.metmuseum.org/public/collection/v1"
    search_resp = get(f"{base}/search", params={"artistOrCulture": "true", "q": source["query"]})
    if search_resp.status_code != 200:
        return [], []
    try:
        ids = search_resp.json().get("objectIDs") or []
    except Exception:
        return [], []

    records, raw = [], []
    for object_id in ids:
        resp = get(f"{base}/objects/{object_id}")
        time.sleep(0.05)
        if resp.status_code != 200:
            continue
        try:
            obj = resp.json()
        except Exception:
            continue
        if not isinstance(obj, dict) or obj.get("artistDisplayName") != source["artist"]:
            continue
        raw.append(obj)
        title = obj.get("title") or "Untitled"
        parts = [f"{title}, {obj.get('objectDate', '')}"]
        for key in ("medium", "dimensions"):
            if obj.get(key):
                parts.append(obj[key])
        parts.append(f"In the collection of The Metropolitan Museum of Art, New York ({obj.get('creditLine', '')})")
        records.append({
            "section": title,
            "text": ". ".join(p.strip().rstrip(".") for p in parts if p.strip()) + ".",
            "url": obj.get("objectURL") or f"https://www.metmuseum.org/art/collection/search/{object_id}",
        })
    return records, raw

def fetch_smithsonian(source):
    key = os.getenv("SI_API_KEY", "DEMO_KEY")
    resp = get(
        "https://api.si.edu/openaccess/api/v1.0/search",
        params={"q": source["query"], "rows": 100, "api_key": key},
    )
    if resp.status_code != 200:
        return [], []
    try:
        rows = resp.json().get("response", {}).get("rows", [])
    except Exception:
        return [], []
    units = set(source.get("units") or [])
    must_contain = (source.get("title_must_contain") or "").lower()
    skip_labels = {"record last modified", "see more items in", "data source", "number of objects in this record"}
    records, raw = [], []
    for row in rows:
        if units and row.get("unitCode") not in units:
            continue
        if must_contain and must_contain not in (row.get("title") or "").lower():
            continue
        content = row.get("content") or {}
        access = (content.get("descriptiveNonRepeating", {}).get("metadata_usage") or {}).get("access")
        if access != "CC0":
            continue
        raw.append(row)
        lines = [row.get("title", "")]
        for items in (content.get("freetext") or {}).values():
            for item in items:
                label, value = item.get("label", "").strip(), " ".join(item.get("content", "").split())
                if value and label.lower() not in skip_labels:
                    lines.append(f"{label}: {value}")
        links = content.get("descriptiveNonRepeating", {})
        records.append({
            "section": row.get("title", ""),
            "text": ". ".join(line.rstrip(".") for line in lines if line) + ".",
            "url": links.get("record_link") or links.get("guid") or "",
        })
    return records, raw

# ---------------------------------------------------------------- chunking

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])[\"')\]]*\s+(?=[A-Z0-9\"'(])")

def clean_text(text):
    """Remove footnote marks like [21], stray citation debris (ref tags, DOI, PMID, PMC and bibcode fragments) and empty brackets left behind by removed markup."""
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"</?ref[^>]*>", " ", text)
    text = re.sub(r"\bdoi:\S+|\bPMC \d+\.?|\bPMID \d+\.?|\b\d{2,4}[A-Za-z&]{2,8}\.{2,}\S*", " ", text)
    text = re.sub(r"\(\s*[;,]?\s*\)", "", text)
    return text

def split_sentences(paragraph):
    return [s.strip() for s in _SENTENCE_SPLIT.split(paragraph) if s.strip()]

def paragraphs_of(text):
    text = text.replace("\r\n", "\n")
    paragraphs = []
    for block in re.split(r"\n\s*\n", text):
        block = " ".join(block.split())
        if len(block.split()) >= 4:
            paragraphs.append(block)
    return paragraphs

def chunk_text(text, target_words=CHUNK_WORDS):
    """Group sentences into passages of about target_words, repeating the last
    sentence of each passage at the start of the next so facts are not cut in half."""
    sentences = []
    for paragraph in paragraphs_of(text):
        for sentence in split_sentences(paragraph):
            words = sentence.split()
            while len(words) > target_words:
                sentences.append(" ".join(words[:target_words]))
                words = words[target_words:]
            if words:
                sentences.append(" ".join(words))

    chunks, current, count = [], [], 0
    for sentence in sentences:
        size = len(sentence.split())
        if current and count + size > target_words:
            chunks.append(" ".join(current))
            last = current[-1]
            current = [last] if len(last.split()) <= MAX_OVERLAP_WORDS else []
            count = sum(len(s.split()) for s in current)
        current.append(sentence)
        count += size
    if current and (not chunks or " ".join(current) != chunks[-1]):
        chunks.append(" ".join(current))
    return chunks

# ---------------------------------------------------------------- building

def source_name(source):
    """The name shown to visitors when an answer cites this source."""
    if source["type"] == "wikipedia":
        return f"Wikipedia: {source['title']}"
    if source.get("title"):
        return source["title"]
    return {
        "artic": "Art Institute of Chicago",
        "met": "The Metropolitan Museum of Art",
        "smithsonian": "Smithsonian Open Access",
    }.get(source["type"], source["type"])

def source_key(source):
    return {
        "gutenberg": f"gut{source.get('id', '')}",
        "wikipedia": "wiki",
        "artic": "aic",
        "met": "met",
        "smithsonian": "si",
    }[source["type"]]

def download(persona, sources_dir):
    """Download every source. Returns {key: {"sections": [...], "url": ..., ...}}."""
    downloaded = {}
    for source in persona["sources"]:
        kind, key = source["type"], source_key(source)
        print(f"  downloading {kind}: {source.get('title') or source.get('query')}")
        if kind == "gutenberg":
            text, url = fetch_gutenberg(source)
            sections, extra = gutenberg_parts(text, source), {}
        elif kind == "wikipedia":
            extract, url, revision = fetch_wikipedia(source)
            sections, extra = wikipedia_sections(extract), {"revision": revision}
        elif kind in ("artic", "met", "smithsonian"):
            fetcher = {"artic": fetch_artic, "met": fetch_met, "smithsonian": fetch_smithsonian}[kind]
            records, raw = fetcher(source)
            (sources_dir / f"{key}_raw.json").write_text(json.dumps(raw, indent=1, ensure_ascii=False), encoding="utf-8")
            sections = [(r["section"], r["text"], r["url"]) for r in records]
            url = {"artic": "https://api.artic.edu/api/v1/artworks/search",
                   "met": "https://collectionapi.metmuseum.org/public/collection/v1/search",
                   "smithsonian": "https://api.si.edu/openaccess/api/v1.0/search"}[kind]
            extra = {"records": len(records)}
        else:
            raise ValueError(f"Unknown source type {kind!r}")
        downloaded[key] = {"source": source, "sections": sections, "url": url, **extra}
    return downloaded

def save_downloads(downloaded, sources_dir):
    manifest = []
    for key, item in downloaded.items():
        path = sources_dir / f"{key}.json"
        payload = json.dumps(item, indent=1, ensure_ascii=False)
        path.write_text(payload, encoding="utf-8")
        manifest.append({
            "key": key, "file": path.name, "url": item["url"],
            "revision": item.get("revision"), "downloaded_on": TODAY,
            "md5": hashlib.md5(payload.encode("utf-8")).hexdigest(),
        })
    (sources_dir / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

def load_downloads(persona, sources_dir):
    manifest_path = sources_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
    download_dates = {entry["key"]: entry.get("downloaded_on") for entry in manifest}
    downloaded = {}
    for source in persona["sources"]:
        key = source_key(source)
        path = sources_dir / f"{key}.json"
        if not path.exists():
            raise FileNotFoundError(f"{path} not found. Run once without --offline first.")
        downloaded[key] = json.loads(path.read_text(encoding="utf-8"))
        # Keep the date the source was actually downloaded, not the date of this rebuild.
        downloaded[key]["downloaded_on"] = download_dates.get(key) or TODAY
    return downloaded

def build(persona_id, offline=False):
    persona = config.load_persona(persona_id)
    folder = config.persona_dir(persona_id)
    sources_dir = folder / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)
    print(f"Building {persona['name']} ({persona_id})")

    downloaded = load_downloads(persona, sources_dir) if offline else download(persona, sources_dir)
    if not offline:
        save_downloads(downloaded, sources_dir)

    chunks, stats = [], []
    for key, item in downloaded.items():
        source = item["source"]
        count_before, words = len(chunks), 0
        for section in item["sections"]:
            name, text = section[0], clean_text(section[1])
            url = section[2] if len(section) > 2 and section[2] else item["url"]
            own_words = bool(section[3]) if len(section) > 3 else False
            for passage in chunk_text(text):
                chunks.append({
                    "id": f"{persona_id}-{key}-{len(chunks) - count_before:04d}",
                    "persona_id": persona_id,
                    "text": passage,
                    "source": source_name(source),
                    "source_type": source["type"],
                    "section": name,
                    "own_words": own_words,
                    "url": url,
                    "licence": source["licence"],
                    "retrieved": item.get("downloaded_on", TODAY),
                })
                words += len(passage.split())
        stats.append({
            "key": key, "type": source["type"],
            "title": source_name(source),
            "licence": source["licence"], "url": item["url"],
            "revision": item.get("revision"),
            "chunks": len(chunks) - count_before, "words_in_chunks": words,
            "own_words_chunks": sum(1 for c in chunks[count_before:] if c["own_words"]),
        })
        print(f"    {key}: {len(chunks) - count_before} passages")

    with open(folder / "chunks.jsonl", "w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    summary = {
        "persona": persona_id, "built_on": TODAY,
        "chunk_words_target": CHUNK_WORDS,
        "total_chunks": len(chunks),
        "total_words_in_chunks": sum(s["words_in_chunks"] for s in stats),
        "sources": stats,
    }
    (folder / "corpus_stats.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"  wrote {len(chunks)} passages to {folder / 'chunks.jsonl'}")
    return summary

def main():
    parser = argparse.ArgumentParser(description="Build the searchable corpus for an exhibit.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--persona", help="exhibit id, e.g. van-gogh")
    group.add_argument("--all", action="store_true", help="build every exhibit in personas/")
    parser.add_argument("--offline", action="store_true", help="rebuild from saved downloads")
    args = parser.parse_args()

    ids = [p["id"] for p in config.list_personas()] if args.all else [args.persona]
    for persona_id in ids:
        build(persona_id, offline=args.offline)

if __name__ == "__main__":
    main()