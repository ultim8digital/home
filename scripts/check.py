#!/usr/bin/env python3
"""Check generated locale coverage, navigation, assets and search metadata."""

import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://ultim8digital.github.io/home/"
APP_BASE = BASE + "anypractice/"


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.ids = []
        self.text = []

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        self.nodes.append((tag, attributes))
        if "id" in attributes:
            self.ids.append(attributes["id"])

    def handle_data(self, data):
        self.text.append(data)

    def find(self, tag, **attributes):
        return [a for t, a in self.nodes if t == tag and all(a.get(k) == v for k, v in attributes.items())]


def check_references(page, path, canonical):
    for tag, attributes in page.nodes:
        ref = attributes.get("src") or (attributes.get("href") if tag in ["link", "a", "use"] else None)
        if not ref or ref.startswith(("mailto:", "https:")):
            continue
        url = urlsplit(urljoin(canonical, ref))
        target = ROOT / "docs" / unquote(url.path.removeprefix("/home/"))
        assert target.exists(), (path, ref)
        if target.is_dir():
            target /= "index.html"
        assert target.is_file(), (path, ref)
        if url.fragment and target.resolve() == path.resolve():
            assert unquote(url.fragment) in page.ids, (path, "missing fragment", ref)


def check_anypractice(locales):
    from anypractice import FIELDS, KINDS
    source = ROOT / "src/anypractice"
    web = json.loads((source / "website-copy.json").read_text())
    native = json.loads((source / "native-copy.json").read_text())
    catalog = json.loads((source / "catalog.json").read_text())
    full = json.loads((source / "privacy-full.json").read_text())
    codes = {l["code"] for l in locales}
    assert set(web) == set(native) == set(catalog) == codes
    assert len(list((ROOT / "docs/anypractice").rglob("*.html"))) == 3 * len(locales)
    assert not list((ROOT / "docs/anypractice").rglob("*.json")), "Source data must not be published"
    expected = {}
    for kind in KINDS:
        expected[kind] = {l["hreflang"]: APP_BASE + l["path"] + kind + ".html" for l in locales}
        expected[kind]["x-default"] = APP_BASE + kind + ".html"
    for locale in locales:
        code = locale["code"]
        assert set(web[code]) == FIELDS
        assert all(isinstance(v, str) and v.strip() for v in web[code].values())
        limits = ''.join(str(unicodedata.digit(c)) if c.isdigit() else c for c in web[code]["pro_limits"])
        assert all(re.search(r'(?<!\d)' + n + r'(?!\d)', limits) for n in ["60", "5"]), (code, "personal generation limits")
        assert not re.search(r'(?<!\d)20(?!\d)', limits), (code, "retired shared request cap")
        prices = ''.join(str(unicodedata.digit(c)) if c.isdigit() else c for c in web[code]["pro_price"]).replace(",", ".").replace("٫", ".")
        assert all(n in prices for n in ["6.99", "49.99"]), (code, "approved prices")
        for kind in KINDS:
            path = ROOT / "docs/anypractice" / locale["path"] / (kind + ".html")
            raw = path.read_text()
            page = Page(); page.feed(raw)
            canonical = APP_BASE + locale["path"] + kind + ".html"
            assert "@@" not in raw and "�" not in raw, path
            assert len(page.ids) == len(set(page.ids)), (path, "duplicate IDs")
            assert len(page.find("h1")) == 1, path
            assert page.find("html")[0]["lang"] == code and page.find("html")[0]["dir"] == locale["dir"]
            assert page.find("link", rel="canonical")[0]["href"] == canonical
            assert page.find("meta", **{"property": "og:url"})[0]["content"] == canonical
            assert page.find("meta", **{"property": "og:locale"})[0]["content"] == locale["og_locale"]
            assert page.find("meta", name="description")[0]["content"].strip()
            assert {a["hreflang"]: a["href"] for a in page.find("link", rel="alternate")} == expected[kind]
            menu = [a for a in page.find("a") if "hreflang" in a]
            assert len(menu) == len(locales)
            assert [a["lang"] for a in menu if a.get("aria-current") == "page"] == [code]
            assert {a["lang"]: urljoin(canonical, a["href"]) for a in menu} == {l["code"]: APP_BASE + l["path"] + kind + ".html" for l in locales}
            assert page.find("a", href="mailto:ultim8digital@gmail.com")
            assert page.find("a", href="https://www.apple.com/legal/internet-services/itunes/dev/stdeula/")
            assert page.find("a", **{"class": "ap-studio"})[0]["href"] == ("../../" if locale["path"] else "../") + locale["path"]
            schema = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)[1])
            assert schema["url"] == canonical and schema["inLanguage"] == code
            assert schema["publisher"]["name"] == "Oleg Korunov"
            assert "offers" not in schema and "aggregateRating" not in schema
            assert not page.find("a", href="https://apps.apple.com/app/id6836826503"), "App is not publicly available yet"
            if kind == "index":
                assert schema["@type"] == "SoftwareApplication"
                assert schema["operatingSystem"] == "iOS 26, iPadOS 26"
                screen_images = [a for a in page.find("img") if "data-screen-language" in a]
                assert len(screen_images) == 5
                assert {a["data-screen-language"] for a in screen_images} == {"ru" if code == "ru" else "en"}
            if kind in ["index", "support"]:
                assert web[code]["pro_label"] in ''.join(page.text), (code, kind, "Pro recommendation")
                assert web[code]["pro_value"] in ''.join(page.text), (code, kind, "Pro benefit")
                assert web[code]["connections"] in ''.join(page.text), (code, kind, "provider access")
            if kind == "support":
                assert web[code]["support_create"] in ''.join(page.text), (code, "generation and saved study")
            if kind == "privacy":
                if code in full:
                    original = Page(); original.feed(full[code])
                    text = ''.join(page.text)
                    assert all(t in text for t in original.text), (code, "preserve published privacy facts")
                else:
                    assert all(s["text"] in ''.join(page.text) for s in native[code]["privacy"]), (code, "native privacy facts")
                    assert web[code]["privacy_extra"] in ''.join(page.text)
                    assert web[code]["privacy_site"] in ''.join(page.text)
                    assert web[code]["connections"] in ''.join(page.text)
                    assert web[code]["apple_access"] in ''.join(page.text)
                    assert web[code]["cloud_scope"] in ''.join(page.text)
            check_references(page, path, canonical)
    return expected


def check():
    locales = json.loads((ROOT / "src/locales.json").read_text())
    apps = json.loads((ROOT / "src/apps.json").read_text())
    app_ids = {a["id"] for a in apps}
    expected = {l["hreflang"]: BASE + l["path"] for l in locales}
    expected["x-default"] = BASE
    for locale in locales:
        path = ROOT / "docs" / locale["path"] / "index.html"
        raw = path.read_text()
        assert "@@" not in raw, path
        page = Page()
        page.feed(raw)
        assert len(page.ids) == len(set(page.ids)), (locale["code"], "duplicate IDs")
        root = page.find("html")[0]
        assert root["lang"] == locale["code"] and root["dir"] == locale["dir"]
        assert page.find("link", rel="canonical")[0]["href"] == BASE + locale["path"]
        assert {a["hreflang"]: a["href"] for a in page.find("link", rel="alternate")} == expected
        menu = [a for a in page.find("a") if "hreflang" in a]
        assert len(menu) == len(locales)
        assert [a["lang"] for a in menu if a.get("aria-current") == "page"] == [locale["code"]]
        assert {a["lang"]: urljoin(BASE + locale["path"], a["href"]) for a in menu} == {l["code"]: BASE + l["path"] for l in locales}
        cards = [a for a in page.find("a") if a.get("class") == "app-card"]
        assert {a["href"] for a in cards} == {
            app.get("website", f'https://ultim8digital.github.io/{app["id"]}/') + locale["path"]
            for app in apps
        }
        assert len(cards) == len(app_ids)
        assert page.find("a", **{"data-app-id": "anypractice"})[0]["href"] == APP_BASE + locale["path"]
        assert page.find("img", **{"class": "orbit-icon orbit-8"})
        chapters = [a for a in page.find("article") if a.get("class") == "story-chapter"]
        assert len(chapters) == 3
        assert len(page.find("button")) == 1, "Catalog must have no filtering controls"
        assert page.find("a", **{"class": "contact-email"})[0]["dir"] == "ltr"
        assert page.find("meta", **{"property": "og:locale"})[0]["content"] == locale["og_locale"]
        check_references(page, path, BASE + locale["path"])
        if locale.get("copy", locale["code"]) != "en":
            for english in ["Skip to content", "Find your next app", "Pause animations", "Back to top"]:
                assert english not in raw, (locale["code"], "untranslated", english)
    app_expected = check_anypractice(locales)
    sitemap = ET.parse(ROOT / "docs/sitemap.xml").getroot()
    assert len(sitemap) == len(locales) * 4
    locations = [e.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text for e in sitemap]
    assert len(locations) == len(set(locations))
    assert set(locations) == set(expected.values()) | {v for group in app_expected.values() for v in group.values()}
    for entry in sitemap:
        location = entry.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
        alternate_expected = app_expected[location.rsplit("/", 1)[-1].removesuffix(".html")] if location.startswith(APP_BASE) else expected
        links = entry.findall("{http://www.w3.org/1999/xhtml}link")
        assert {l.attrib["hreflang"]: l.attrib["href"] for l in links} == alternate_expected
    print(f'PASS: {len(locales)} Home locales, {len(locales) * len(app_ids)} app links, {len(locales) * 3} AnyPractice pages, privacy facts, local assets, RTL, language navigation and {len(sitemap)} sitemap entries')


if __name__ == "__main__":
    check()
