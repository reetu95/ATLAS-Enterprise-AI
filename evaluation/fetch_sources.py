"""Download fixed public handbook text; never execute document content."""
import hashlib
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
SOURCES = {
    'time-away': 'https://handbook.gitlab.com/handbook/people-group/time-off-and-absence/time-away-philosophy/',
    'time-off': 'https://handbook.gitlab.com/handbook/people-group/time-off-and-absence/',
    'communication': 'https://handbook.gitlab.com/handbook/communication/',
    'handbook-first': 'https://handbook.gitlab.com/handbook/company/culture/all-remote/handbook-first/',
    'meetings': 'https://handbook.gitlab.com/handbook/company/culture/all-remote/meetings/',
}

class Content(HTMLParser):
    def __init__(self):
        super().__init__(); self.depth = 0; self.parts = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if not self.depth and tag == 'div' and 'td-content' in attrs.get('class', '').split():
            self.depth = 1
        elif self.depth and tag == 'div':
            self.depth += 1
        if self.depth and tag in ('p','li','h1','h2','h3','h4','br','tr'):
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if self.depth and tag == 'div': self.depth -= 1
        if self.depth and tag in ('p','li','h1','h2','h3','h4','tr'):
            self.parts.append('\n')
    def handle_data(self, data):
        if self.depth: self.parts.append(data)

def main():
    folder = ROOT / 'corpus'; folder.mkdir(exist_ok=True)
    manifest = []
    for name, url in SOURCES.items():
        request = Request(url, headers={'User-Agent': 'ATLAS-portfolio-evaluation/1.0'})
        with urlopen(request, timeout=60) as response:
            parser = Content(); parser.feed(response.read().decode('utf-8'))
            final_url = response.url
        text = '\n'.join(line.strip() for line in ''.join(parser.parts).splitlines() if line.strip())
        if len(text) < 500: raise ValueError(f'No substantial article content: {url}')
        content = f'Source: {final_url}\nSnapshot date: 2026-11-18\n\n{text}\n'
        path = folder / f'{name}.txt'; path.write_text(content, encoding='utf-8')
        manifest.append({'id': name, 'url': final_url, 'file': path.name,
                         'fetched_at': datetime.now(timezone.utc).isoformat(),
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        print(f'{name}: {len(text)} characters')
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')

if __name__ == '__main__': main()
