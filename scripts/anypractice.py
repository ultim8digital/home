"""Build the public AnyPractice product, support and privacy pages."""

import hashlib
import html
import json
import re
import shutil
from pathlib import Path

from localization import load_copy

BASE = "https://ultim8digital.github.io/home/anypractice/"
EMAIL = "ultim8digital@gmail.com"
TERMS = "https://www.apple.com/legal/internet-services/itunes/dev/stdeula/"
DATA = "https://developers.openai.com/api/docs/guides/your-data"
COUNTRIES = "https://developers.openai.com/api/docs/supported-countries"
KINDS = ("index", "support", "privacy")
FIELDS = {
    "hero_title", "hero_action", "launch", "features_title",
    "feature_1_title", "feature_1_text", "feature_2_title", "feature_2_text",
    "feature_3_title", "feature_3_text", "screen_note", "choice_title",
    "connections", "pro_limits", "pro_price", "support_intro", "support_create",
    "support_scan", "privacy_extra_title", "privacy_extra", "privacy_site",
    "updated", "contents", "studio", "apple_access", "cloud_scope", "pro_label", "pro_value",
}


def esc(text):
    return html.escape(str(text), quote=True)


def version(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def alternates(locales, kind, xml=False):
    tag = "xhtml:link" if xml else "link"
    pairs = [(l["hreflang"], BASE + l["path"] + kind + ".html") for l in locales]
    pairs.append(("x-default", BASE + kind + ".html"))
    return "\n".join('<{tag} rel="alternate" hreflang="{lang}" href="{url}"{end}>'.format(
        tag=tag, lang=lang, url=esc(url), end="/" if xml else "") for lang, url in pairs)


def language_picker(locales, locale, kind, label):
    prefix = "../" if locale["path"] else "./"
    links = []
    for other in locales:
        links.append('<a href="{}" lang="{}" hreflang="{}" dir="auto"{}>{}</a>'.format(
            esc(prefix + other["path"] + kind + ".html"), other["code"], other["hreflang"],
            ' aria-current="page"' if other["code"] == locale["code"] else "", esc(other["name"])))
    return ('<details class="language-picker"><summary aria-label="{label}: {name}">'
            '<span aria-hidden="true">◎</span><bdi class="language-current">{name}</bdi>'
            '<span class="language-short" aria-hidden="true">{short}</span>'
            '<span class="language-chevron" aria-hidden="true">⌄</span></summary>'
            '<nav class="languages" aria-label="{label}">{links}</nav></details>').format(
                label=esc(label), name=esc(locale["name"]), short=esc(locale["code"].upper()), links="".join(links))


def phone(asset, lang, image, label, class_name="", lazy=True):
    return '<div class="ap-phone {}"><img src="{}screens/{}/{}.webp" width="600" height="1304" alt="{}" data-screen-language="{}" decoding="async" {}></div>'.format(
        class_name, asset, lang, image, esc(label), lang, 'loading="lazy"' if lazy else 'fetchpriority="high"')


def landing(asset, native, web, catalog, screen_language):
    label = native["labels"]
    book = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 6c-4-3-8-2-10-1v15c3-2 7-2 10 0 3-2 7-2 10 0V5c-3-1-6-2-10 1Zm0 0v14"/></svg>'
    sheet = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h12v18H5V3h2Zm1 5h8M8 12h8M8 16h5"/></svg>'
    check = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2" y="3" width="20" height="18" rx="5"/><path d="m7 12 4 4 7-8"/></svg>'
    features = []
    for index, image in enumerate(["lesson", "sheet", "practice"], 1):
        screen_label = label[["Lesson", "Cheat sheet", "Practice"][index - 1]]
        features.append('<article class="ap-feature" data-ap-reveal><div class="ap-screen-well">'
                        '<span class="ap-screen-lang" lang="en">{language}</span>{phone}</div>'
                        '<div class="ap-feature-copy"><h3>{title}</h3><p>{text}</p></div></article>'.format(
                            language=screen_language.upper(), phone=phone(asset, screen_language, image, screen_label),
                            title=esc(web[f"feature_{index}_title"]), text=esc(web[f"feature_{index}_text"])))
    return '''<main id="main">
  <section class="ap-hero ap-wrap" aria-labelledby="hero-title">
    <div class="ap-hero-copy">
      <p class="ap-kicker"><span class="ap-dot" aria-hidden="true"></span>{kicker}</p>
      <h1 id="hero-title">{title}</h1><p class="ap-intro">{intro}</p>
      <div class="ap-actions"><a class="ap-button" href="#tour">{cta} <span aria-hidden="true">↓</span></a><a class="ap-link" href="support.html">{support} <span aria-hidden="true">↗</span></a></div>
      <p class="ap-availability"><svg viewBox="0 0 20 24" fill="currentColor" aria-hidden="true"><path d="M14 0c.3 2.4-1.4 4.5-3.5 4.8C10.1 2.6 11.7.4 14 0ZM17.8 17.7c-.8 1.8-2.2 4.8-4.2 4.9-1.2 0-1.7-.8-3.2-.8-1.6 0-2.2.8-3.4.8-2-.1-3.5-2.9-4.3-4.7C.3 12.6 2 6.5 6.1 6.2c1.5-.1 2.9.9 3.8.9.9 0 2.6-1.1 4.4-.9 1 .1 3 .5 4.2 2.4-3.7 2-3.1 7.2-.7 9.1Z"/></svg><span>iPhone &amp; iPad · iOS / iPadOS 26+ · {launch}</span></p>
    </div>
    <figure class="ap-visual" aria-label="{screen_note}" data-screenshot-lang="{screen_language}"><div class="ap-art">
      {main_phone}{side_phone}<svg class="ap-spark" viewBox="0 0 100 100" aria-hidden="true"><path d="M50 0C59 32 68 41 100 50 68 59 59 68 50 100 41 68 32 59 0 50 32 41 41 32 50 0Z"/></svg>
      <span class="ap-file" aria-hidden="true">PDF</span></div><figcaption class="ap-art-label"><span dir="auto">{screen_note} <bdi lang="en">({screen_language})</bdi></span></figcaption>
    </figure>
  </section>
  <div class="ap-strip"><div class="ap-wrap ap-strip-inner"><span>{book}{lesson}</span><span>{sheet}{cheat}</span><span>{check}{practice}</span></div></div>
  <section class="ap-section ap-features" id="tour" aria-labelledby="tour-title"><div class="ap-wrap">
    <div class="ap-section-heading"><h2 id="tour-title">{features_title}</h2><p class="ap-small-note">{screen_note}</p></div>
    <div class="ap-feature-grid">{features}</div>
  </div></section>
  <section class="ap-section ap-wrap ap-choice" aria-labelledby="choice-title">
    <div data-ap-reveal><p class="ap-kicker">AnyPractice</p><h2 id="choice-title">{choice_title}</h2><p class="ap-choice-copy">{privacy_summary}</p><a class="ap-link" href="privacy.html">{privacy} <span aria-hidden="true">↗</span></a></div>
    <div class="ap-connection-list">
      <article class="ap-connection" data-ap-reveal><h3>{providers}</h3><p>{connections}</p></article>
      <article class="ap-connection" data-ap-reveal><h3>{pro_label}</h3><p>{pro_value}</p><p>{limits}</p><p class="ap-price">{price}</p><a class="ap-policy-link" href="{countries}" lang="en">OpenAI — supported countries ↗</a></article>
    </div>
  </section>
  <section class="ap-bottom"><div class="ap-wrap ap-bottom-inner"><h2>{contact_title}</h2><a class="ap-button" href="support.html">{support} <span aria-hidden="true">↗</span></a></div></section>
</main>'''.format(
        kicker=esc(label["A LITTLE PRACTICE, EVERY DAY"]), title=esc(web["hero_title"]), intro=esc(catalog["description"]),
        cta=esc(web["hero_action"]), support=esc(label["Support"]), launch=esc(web["launch"]),
        screen_note=esc(web["screen_note"]), screen_language=screen_language,
        main_phone=phone(asset, screen_language, "lesson", label["Lesson"], "ap-phone-main", False),
        side_phone=phone(asset, screen_language, "practice", label["Practice"], "ap-phone-side", False),
        book=book, sheet=sheet, check=check, lesson=esc(label["Lesson"]), cheat=esc(label["Cheat sheet"]), practice=esc(label["Practice"]),
        features_title=esc(web["features_title"]), features="".join(features), choice_title=esc(web["choice_title"]),
        privacy_summary=esc(native["privacy"][1]["text"]), privacy=esc(label["Privacy policy"]), providers=esc(label["AI providers"]),
        connections=esc(web["connections"]), pro_label=esc(web["pro_label"]), pro_value=esc(web["pro_value"]), limits=esc(web["pro_limits"]), price=esc(web["pro_price"]), countries=COUNTRIES,
        contact_title=esc(label["Contact support"]))


def document(kind, native, web, full_policy):
    label = native["labels"]
    if kind == "privacy":
        sections = []
        if full_policy:
            chunks = re.split(r"<h2>(.*?)</h2>", full_policy, flags=re.S)
            for index in range(1, len(chunks), 2):
                sections.append((chunks[index], chunks[index + 1]))
        else:
            for index, section in enumerate(native["privacy"]):
                prefix = {2: web["connections"], 3: web["apple_access"], 4: web["cloud_scope"]}.get(index, "")
                paragraph = (prefix + " " if prefix else "") + section["text"]
                sections.append((esc(section["title"]), "<p>" + esc(paragraph) + "</p>"))
        if not full_policy:
            sections.extend([
                (esc(web["privacy_extra_title"]), "<p>" + esc(web["privacy_extra"]) + '</p><p><a href="' + DATA + '" lang="en">OpenAI API data controls ↗</a></p>'),
                (esc(label["Support"]), "<p>" + esc(web["privacy_site"]) + '</p><p><a href="mailto:' + EMAIL + '">' + EMAIL + "</a></p>"),
            ])
        contents = []; body = []
        for index, (title, text) in enumerate(sections, 1):
            section_id = "privacy-" + str(index)
            contents.append('<a href="#{}">{}</a>'.format(section_id, title))
            body.append('<section id="{}"><h2>{}</h2>{}</section>'.format(section_id, title, text))
        return '''<main id="main" class="ap-wrap"><div class="ap-doc-hero"><p class="ap-kicker">{updated}</p><h1>{title}</h1><p class="ap-intro">{choice}</p><p class="ap-small-note">AnyPractice · Oleg Korunov / ULTIMATE DIGITAL · <a href="mailto:{email}" dir="ltr">{email}</a></p></div>
<div class="ap-doc-grid"><aside class="ap-toc"><strong>{toc}</strong><nav aria-label="{toc}">{contents}</nav></aside><article class="ap-document">{body}<div class="ap-doc-footer"><a href="support.html">{support}</a><a href="{terms}">{terms_label}</a></div></article></div></main>'''.format(
            updated=esc(web["updated"]), title=esc(label["Privacy policy"]), choice=esc(web["choice_title"]), email=EMAIL,
            toc=esc(web["contents"]), contents="".join(contents), body="".join(body), support=esc(label["Support"]), terms=TERMS, terms_label=esc(label["Terms of use"]))
    faq = [
        (label["Your material"], [web["support_create"]]),
        (label["Photos and PDFs"], [web["support_scan"]]),
        (web["pro_label"], [web["pro_value"], web["pro_limits"], web["pro_price"], web["connections"]]),
        (label["Report generated content"], [native["report"]]),
        (label["Remove saved data"], [native["privacy"][-1]["text"]]),
    ]
    items = []
    for index, (title, paragraphs) in enumerate(faq):
        items.append('<details id="help-{}"{}><summary>{}</summary>{}</details>'.format(index, " open" if index == 0 else "", esc(title), "".join("<p>" + esc(p) + "</p>" for p in paragraphs)))
    return '''<main id="main" class="ap-wrap"><div class="ap-doc-hero"><p class="ap-kicker">AnyPractice</p><h1>{title}</h1></div>
<div class="ap-doc-grid"><aside class="ap-toc"><strong>{toc}</strong><nav aria-label="{toc}">{links}</nav></aside><div class="ap-document"><div class="ap-contact-card"><a href="mailto:{email}?subject=AnyPractice%20support" dir="ltr">{email} <span aria-hidden="true">↗</span></a><p>{intro}</p></div><div class="ap-faq">{items}</div><div class="ap-doc-footer"><a href="privacy.html">{privacy}</a><a href="mailto:{email}?subject=AnyPractice%20content%20report">{report}</a><a href="{terms}">{terms_label}</a></div></div></div></main>'''.format(
        title=esc(label["Support"]), intro=esc(web["support_intro"]), toc=esc(web["contents"]),
        links="".join('<a href="#help-{}">{}</a>'.format(i, esc(t)) for i, (t, _) in enumerate(faq)),
        email=EMAIL, items="".join(items), privacy=esc(label["Privacy policy"]), report=esc(label["Report generated content"]), terms=TERMS, terms_label=esc(label["Terms of use"]))


def build_anypractice(source, output, locales, web_copy=None):
    app_source = source / "anypractice"
    app_output = output / "anypractice"
    native = json.loads((app_source / "native-copy.json").read_text())
    catalog = json.loads((app_source / "catalog.json").read_text())
    web = web_copy if web_copy is not None else json.loads((app_source / "website-copy.json").read_text())
    full = json.loads((app_source / "privacy-full.json").read_text())
    requested = {l["code"] for l in locales}
    assert requested <= set(native) and requested <= set(catalog)
    assert set(web) == requested, "AnyPractice website copy must cover the requested locales exactly"
    for code in web:
        assert set(web[code]) == FIELDS, (code, "website copy fields")
        assert all(isinstance(v, str) and v.strip() for v in web[code].values()), code
    if app_output.exists():
        shutil.rmtree(app_output)
    app_output.mkdir()
    for name in ["style.css", "site.js", "icon.png", "icon.webp", "favicon.png"]:
        shutil.copy2(app_source / name, app_output / name)
    shutil.copytree(app_source / "screens", app_output / "screens", dirs_exist_ok=True)
    apps = json.loads((source / "apps.json").read_text())
    entries = []
    for locale in locales:
        code = locale["code"]
        label = native[code]["labels"]
        shared, _ = load_copy(source, locale, apps)
        asset = "../" if locale["path"] else "./"
        root = "../../" if locale["path"] else "../"
        screen_language = "ru" if code == "ru" else "en"
        destination = app_output / locale["path"]
        destination.mkdir(exist_ok=True)
        for kind in KINDS:
            canonical = BASE + locale["path"] + kind + ".html"
            title = "AnyPractice — " + (catalog[code]["tag"] if kind == "index" else label["Support" if kind == "support" else "Privacy policy"])
            description = catalog[code]["description"] if kind == "index" else (web[code]["support_intro"] if kind == "support" else native[code]["privacy"][0]["text"])
            structured = {
                "@context": "https://schema.org", "@type": "SoftwareApplication" if kind == "index" else "WebPage",
                "name": "AnyPractice" if kind == "index" else title, "url": canonical, "inLanguage": code,
                "description": description,
                "publisher": {"@type": "Person", "name": "Oleg Korunov", "email": EMAIL},
            }
            if kind == "index":
                structured.update(applicationCategory="EducationalApplication", operatingSystem="iOS 26, iPadOS 26", image=BASE + "icon.png")
            nav = []
            for file, text in [("index", label["About"]), ("support", label["Support"]), ("privacy", label["Privacy policy"])]:
                nav.append('<a href="{}.html"{}>{}</a>'.format(file, ' aria-current="page"' if file == kind else "", esc(text)))
            body = landing(asset, native[code], web[code], catalog[code], screen_language) if kind == "index" else document(kind, native[code], web[code], full.get(code) if kind == "privacy" else None)
            rendered = '''<!doctype html>
<html class="ap-site" lang="{lang}" dir="{direction}" data-script="{script}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#fbfaf4"><title>{title}</title><meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
{alternates}
<meta property="og:type" content="website"><meta property="og:site_name" content="AnyPractice"><meta property="og:title" content="{title}"><meta property="og:description" content="{description}"><meta property="og:url" content="{canonical}"><meta property="og:locale" content="{og_locale}"><meta property="og:image" content="{base}icon.png"><meta property="og:image:alt" content="AnyPractice"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="{title}"><meta name="twitter:description" content="{description}"><meta name="twitter:image" content="{base}icon.png">
<link rel="icon" href="{asset}favicon.png" type="image/png"><link rel="preload" href="{root}assets/fonts/Onest-Variable.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="{root}assets/locales.css?v={locale_version}"><link rel="stylesheet" href="{asset}style.css?v={style_version}">
<script type="application/ld+json">{structured}</script><script src="{asset}site.js?v={js_version}" defer></script>
</head><body>
<a class="ap-skip" href="#main">{skip}</a>
<header class="ap-header"><div class="ap-wrap ap-header-inner"><a class="ap-brand" href="index.html" aria-label="AnyPractice"><img src="{asset}icon.webp" width="43" height="43" alt="">AnyPractice</a><nav class="ap-nav" aria-label="AnyPractice">{nav}</nav><div class="ap-utils"><button class="ap-motion" type="button" aria-pressed="false" aria-label="{pause}" data-pause="{pause}" data-resume="{resume}" hidden><svg data-pause viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M7 4v12M13 4v12"/></svg><svg data-play viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" style="display:none"><path d="m6 3 11 7-11 7Z"/></svg></button>{languages}</div></div><div class="ap-progress" aria-hidden="true"></div></header>
{body}
<footer class="ap-footer"><div class="ap-wrap ap-footer-inner"><div class="ap-footer-brand">AnyPractice<small>© 2026 Oleg Korunov · ULTIMATE DIGITAL</small></div><nav aria-label="AnyPractice"><a href="support.html">{support}</a><a href="privacy.html">{privacy}</a><a href="{terms}">{terms_label}</a><a href="mailto:{email}" dir="ltr">{email}</a></nav><a class="ap-studio" href="{studio_url}">{studio} <span aria-hidden="true">↗</span></a></div></footer>
</body></html>
'''.format(
                lang=code, direction=locale["dir"], script=locale["script"], title=esc(title), description=esc(description), canonical=esc(canonical),
                alternates=alternates(locales, kind), og_locale=locale["og_locale"], base=BASE, asset=asset, root=root,
                locale_version=version(source / "assets/locales.css"), style_version=version(app_source / "style.css"), js_version=version(app_source / "site.js"),
                structured=json.dumps(structured, ensure_ascii=False).replace("</", "<\\/"), skip=esc(shared["skip"]), nav="".join(nav),
                pause=esc(shared["motion_pause"]), resume=esc(shared["motion_resume"]), languages=language_picker(locales, locale, kind, label["Language"]), body=body,
                support=esc(label["Support"]), privacy=esc(label["Privacy policy"]), terms=TERMS, terms_label=esc(label["Terms of use"]), email=EMAIL,
                studio_url=root + locale["path"], studio=esc(web[code]["studio"]))
            (destination / (kind + ".html")).write_text(rendered, encoding="utf-8")
            entries.append("  <url><loc>" + esc(canonical) + "</loc>" + alternates(locales, kind, xml=True) + "</url>\n")
    print("Built AnyPractice: {} locales × 3 pages".format(len(locales)))
    return "".join(entries)
