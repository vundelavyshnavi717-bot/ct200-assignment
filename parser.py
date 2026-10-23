import hashlib, re
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ParsedNode:
    heading: str
    level: int
    body: list[str] = field(default_factory=list)
    children: list['ParsedNode'] = field(default_factory=list)
    node_type: str = 'section'

_NUM = re.compile(r'^(?P<num>\d+(?:\.\d+)*)(?:[.)])?\s+(?P<title>.+?)\s*$')

def content_hash(heading: str, body: list[str]) -> str:
    normalized = heading.strip() + '\n' + '\n'.join(x.strip() for x in body).strip()
    return hashlib.sha256(normalized.encode()).hexdigest()

def _heading(line: str):
    s = line.strip().strip('#').strip()
    m = _NUM.match(s)
    if not m: return None
    num = m.group('num')
    # Numbering determines hierarchy, while formatting is only a hint.
    return num, m.group('title').strip(), len(num.split('.'))

def parse_text(text: str) -> list[ParsedNode]:
    roots: list[ParsedNode] = []
    stack: list[tuple[int, ParsedNode]] = []
    pending: list[str] = []
    def attach(node):
        nonlocal stack
        while stack and stack[-1][0] >= node.level: stack.pop()
        if stack: stack[-1][1].children.append(node)
        else: roots.append(node)
        stack.append((node.level, node))
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line == '---': continue
        h = _heading(line)
        if h:
            if pending and stack: stack[-1][1].body.extend(pending)
            pending = []
            num, title, level = h
            node = ParsedNode(heading=f'{num} {title}', level=level)
            attach(node)
        elif line == '-':
            # A stray list marker is retained as an explicit unsupported fragment.
            pending.append('-')
        else:
            pending.append(line)
    if pending and stack: stack[-1][1].body.extend(pending)
    return roots

def extract_pdf(path: str) -> list[ParsedNode]:
    try:
        from pypdf import PdfReader
        text = '\n'.join((p.extract_text() or '') for p in PdfReader(path).pages)
    except Exception as exc:
        raise RuntimeError(f'PDF extraction failed; provide OCR text for this file: {exc}') from exc
    return parse_text(text)

def flatten(nodes: list[ParsedNode], parent_key=None):
    for idx, n in enumerate(nodes):
        # Duplicate headings remain distinct because ordinal and parent are in the key.
        key = f'{parent_key or "root"}/{idx}:{n.heading}'
        yield key, n
        yield from flatten(n.children, key)
