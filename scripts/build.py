#!/usr/bin/env python3
"""Build every localized GitHub Pages entry point using Python's stdlib."""

import html
import hashlib
import json
import re
import shutil
from pathlib import Path
from localization import load_copy
from anypractice import build_anypractice

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
OUTPUT = ROOT / "docs"
BASE_URL = "https://ultim8digital.github.io/home/"


def escape(value):
    return html.escape(str(value), quote=True)


def make_cards(apps, locale, prefix, copy, localized, tags):
    cards = []
    language = locale["code"]
    for app in apps:
        website = app.get("website", "https://ultim8digital.github.io/{}/".format(app["id"])) + locale["path"]
        content = ({key: app[key][language] for key in ["name", "description"]}
                   if language in ["en", "ru"] else localized[language][app["id"]])
        name = escape(content["name"])
        cards.append(
            '<a class="app-card" data-reveal data-app-category="{category}" data-app-id="{id}" '
            'style="--app-color:{color}" href="{url}" '
            'aria-label="{label} {name}">'
            '<div class="app-card-top">'
            '<img class="app-icon" src="{prefix}assets/icons/{id}.jpg" '
            'width="76" height="76" alt="" loading="lazy" decoding="async">'
            '<span class="app-tag">{tag}</span></div>'
            '<h3><bdi>{name}</bdi></h3><p class="app-description">{description}</p>'
            '<span class="app-card-bottom"><span>{visit}</span>'
            '<span class="app-card-arrow" aria-hidden="true">↗</span></span></a>'.format(
                category=escape(app["category"]),
                color=escape(app["color"]),
                url=escape(website),
                label=escape(copy["visit_label"]),
                name=name,
                prefix=prefix,
                id=escape(app["id"]),
                tag=escape(tags[app["id"]]),
                description=escape(content["description"]),
                visit=escape(copy["visit"]),
            )
        )
    return "\n".join(cards)


def make_story(locale, prefix, copy):
    chapters, scenes = [], []
    language = locale["code"]
    # Product screens are unmodified source assets. Other editions reuse English
    # screens, while the surrounding story and links use the selected language.
    preview_language = "ru" if language == "ru" else "en"
    for index, (topic, app) in enumerate([
        ("learn", "periodic-table"),
        ("move", "unlocky"),
        ("play", "im-bored"),
    ]):
        images = list((SOURCE / "assets" / "story").glob(topic + "-" + preview_language + ".*"))
        if len(images) != 1:
            raise ValueError("Expected one product preview for " + topic + " / " + language)
        image = escape(prefix + "assets/story/" + images[0].name)
        url = "https://ultim8digital.github.io/{}/{}".format(app, locale["path"])
        field = lambda suffix: escape(copy["story_" + topic + "_" + suffix]).replace("\n", "<br>")
        device = '<div class="story-device"><img src="{}" width="600" height="1300" alt="{}" loading="lazy" decoding="async"></div>'
        chapters.append(
            '<article class="story-chapter" data-chapter="{index}" data-reveal>'
            '<div class="chapter-copy"><p class="chapter-label">{label}</p>'
            '<h3>{title}</h3><p class="chapter-description">{description}</p>'
            '<a class="chapter-link" href="{url}">{link} <span aria-hidden="true">↗</span></a></div>'
            '<figure class="chapter-preview">{device}</figure></article>'.format(
                index=index, label=field("label"), title=field("title"),
                description=field("description"), url=escape(url), link=field("link"),
                device=device.format(image, field("alt")),
            )
        )
        scenes.append(
            '<div class="story-scene{active}" data-scene="{index}">'
            '{device}'
            '<img class="scene-badge" src="{prefix}assets/icons/{app}.jpg" width="76" height="76" alt="" loading="lazy">'
            '</div>'.format(
                active=" is-active" if index == 0 else "", index=index,
                device=device.format(image, ""), prefix=prefix, app=app,
            )
        )
    return "\n".join(chapters), "\n".join(scenes)


def make_languages(locales, locale, prefix, copy):
    links = []
    for other in locales:
        links.append('<a href="{url}" lang="{lang}" hreflang="{hreflang}" dir="auto"{current}>{name}</a>'.format(
            url=escape(prefix + other["path"] or "./"), lang=other["code"],
            hreflang=other["hreflang"], name=escape(other["name"]),
            current=' aria-current="page"' if other["code"] == locale["code"] else ""))
    return ('<details class="language-picker"><summary aria-label="{label}: {name}">'
            '<span aria-hidden="true">◎</span><bdi class="language-current" lang="{code}">{name}</bdi>'
            '<span class="language-short" aria-hidden="true">{short}</span>'
            '<span class="language-chevron" aria-hidden="true">⌄</span></summary>'
            '<nav class="languages" aria-label="{label}">{links}</nav></details>').format(
                label=escape(copy["language_label"]), name=escape(locale["name"]),
                code=locale["code"], short=escape(locale["code"].upper()), links="".join(links))


def make_alternates(locales, xml=False):
    tag = "xhtml:link" if xml else "link"
    entries = [(l["hreflang"], BASE_URL + l["path"]) for l in locales] + [("x-default", BASE_URL)]
    return "\n".join('<{tag} rel="alternate" hreflang="{lang}" href="{url}"{end}>'.format(
        tag=tag, lang=lang, url=escape(url), end="/" if xml else "") for lang, url in entries)


def build():
    apps = json.loads((SOURCE / "apps.json").read_text(encoding="utf-8"))
    locales = json.loads((SOURCE / "locales.json").read_text(encoding="utf-8"))
    localized = json.loads((SOURCE / "app-localizations.json").read_text(encoding="utf-8"))
    template = (SOURCE / "index.template.html").read_text(encoding="utf-8")
    ids = [app["id"] for app in apps]
    if len(ids) != len(set(ids)):
        raise ValueError("App IDs must be unique")
    for app in apps:
        if not re.fullmatch(r"[a-z0-9-]+", app["id"]):
            raise ValueError("Use the published app website's repository slug as its ID")
        if not re.fullmatch(r"#[a-fA-F0-9]{6}", app["color"]):
            raise ValueError("App colors must be hexadecimal colors")
        if not (SOURCE / "assets" / "icons" / (app["id"] + ".jpg")).is_file():
            raise ValueError("Missing icon for " + app["id"])

    for key in ["code", "path", "hreflang"]:
        if len({locale[key] for locale in locales}) != len(locales):
            raise ValueError("Duplicate locale " + key)
    if set(localized) != {locale["code"] for locale in locales}:
        raise ValueError("App translations must cover exactly the supported locales")
    for locale in locales:
        code, path = locale["code"], locale["path"]
        if path != ("" if code == "en" else code + "/") or not re.fullmatch(r"[a-z]{2}(?:-[A-Za-z0-9]+)?", code):
            raise ValueError("Invalid locale route: " + code)
        if locale["dir"] not in ["ltr", "rtl"]:
            raise ValueError("Invalid text direction: " + code)
        if set(localized[code]) != set(ids):
            raise ValueError("Incomplete app catalog: " + code)
        for content in localized[code].values():
            if set(content) != {"name", "description"} or not all(isinstance(v, str) and v.strip() for v in content.values()):
                raise ValueError("Incomplete app translation: " + code)

    OUTPUT.mkdir(exist_ok=True)
    shutil.copytree(SOURCE / "assets", OUTPUT / "assets", dirs_exist_ok=True)
    for locale in locales:
        language = locale["code"]
        copy, tags = load_copy(SOURCE, locale, apps)
        prefix = "../" if locale["path"] else ""
        canonical = BASE_URL + locale["path"]
        values = {key: escape(value.replace("Ultimate Digital", "ULTIMATE DIGITAL")).replace("\n", "<br>") for key, value in copy.items()}
        structured_data = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "ULTIMATE DIGITAL",
            "url": BASE_URL,
            "logo": BASE_URL + "assets/favicon.svg",
            "email": "ultim8digital@gmail.com",
            "sameAs": ["https://github.com/ultim8digital"],
        }
        chapters, scenes = make_story(locale, prefix, copy)
        values.update({
            "lang": language,
            "direction": locale["dir"],
            "locale_script": locale["script"],
            "canonical": escape(canonical),
            "asset_prefix": prefix,
            "home_path": "./",
            "language_picker": make_languages(locales, locale, prefix, copy),
            "alternate_links": make_alternates(locales),
            "og_locale": locale["og_locale"],
            "app_count": str(len(apps)),
            "app_cards": make_cards(apps, locale, prefix, copy, localized, tags),
            "story_chapters": chapters,
            "story_scenes": scenes,
            "motion_css_version": hashlib.sha256((SOURCE / "assets/motion.css").read_bytes()).hexdigest()[:10],
            "motion_js_version": hashlib.sha256((SOURCE / "assets/motion.js").read_bytes()).hexdigest()[:10],
            "site_css_version": hashlib.sha256((SOURCE / "assets/site.css").read_bytes()).hexdigest()[:10],
            "locale_css_version": hashlib.sha256((SOURCE / "assets/locales.css").read_bytes()).hexdigest()[:10],
            "locale_js_version": hashlib.sha256((SOURCE / "assets/locales.js").read_bytes()).hexdigest()[:10],
            "social_image_version": hashlib.sha256((SOURCE / "assets/social-card.png").read_bytes()).hexdigest()[:10],
            "structured_data": json.dumps(structured_data, ensure_ascii=False).replace("</", "<\\/"),
        })

        def substitute(match):
            return values[match.group(1)]

        rendered = re.sub(r"@@([a-z_0-9]+)@@", substitute, template)
        if "@@" in rendered:
            raise ValueError("Unresolved template token")
        destination = OUTPUT / locale["path"] / "index.html"
        destination.parent.mkdir(exist_ok=True)
        destination.write_text(rendered, encoding="utf-8")
        print("Built " + str(destination.relative_to(ROOT)))

    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")
    anypractice_entries = build_anypractice(SOURCE, OUTPUT, locales)
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
    sitemap += 'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    for locale in locales:
        sitemap += '  <url><loc>' + BASE_URL + locale["path"] + '</loc>'
        sitemap += make_alternates(locales, xml=True) + '</url>\n'
    sitemap += anypractice_entries
    sitemap += '</urlset>\n'
    (OUTPUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    not_found = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Page not found — ULTIMATE DIGITAL</title>
<link rel="icon" href="/home/assets/favicon.svg"><link rel="stylesheet" href="/home/assets/site.css"></head>
<body><main class="container" style="padding-block:100px;max-width:760px">
<p class="eyebrow">ULTIMATE DIGITAL / 404</p><h1 style="font-size:clamp(48px,8vw,80px)">A little off track.</h1>
<p class="hero-description">This page has moved or doesn't exist. Your next discovery is back at the studio.</p>
<p class="hero-description" lang="ru">Страница не найдена. Вернитесь на главную — там есть что посмотреть.</p>
<div class="hero-actions"><a class="button button-primary" href="/home/">Back to home ↗</a>
<a class="text-link" href="/home/ru/" lang="ru">На главную →</a></div></main></body></html>'''
    (OUTPUT / "404.html").write_text(not_found, encoding="utf-8")
    print("Ready: {} apps, {} locales".format(len(apps), len(locales)))


if __name__ == "__main__":
    build()
