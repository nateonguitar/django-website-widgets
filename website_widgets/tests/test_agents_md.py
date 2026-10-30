import os
import re

from django.test import SimpleTestCase


PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(PACKAGE_DIR, 'docs')
AGENTS_MD_PATH = os.path.join(DOCS_DIR, 'AGENTS.md')
INDEX_LINE_RE = re.compile(r'^- `([^`/]+\.md)` — \S', re.MULTILINE)


class AgentsMdTestCase(SimpleTestCase):
    def indexed_docs(self) -> list[str]:
        with open(AGENTS_MD_PATH) as agents_md:
            return INDEX_LINE_RE.findall(agents_md.read())

    def test_agents_md__indexes_every_doc__when_a_doc_is_in_docs(self):
        docs = sorted(
            filename
            for filename in os.listdir(DOCS_DIR)
            if filename.endswith('.md') and filename != 'AGENTS.md'
        )

        self.assertEqual(sorted(self.indexed_docs()), docs)

    def test_agents_md__names_only_existing_docs__when_indexing(self):
        for doc in self.indexed_docs():
            with self.subTest(doc=doc):
                self.assertTrue(os.path.isfile(os.path.join(DOCS_DIR, doc)))

    def test_agents_md__indexes_each_doc_once__when_indexing(self):
        indexed_docs = self.indexed_docs()

        self.assertEqual(len(indexed_docs), len(set(indexed_docs)))
