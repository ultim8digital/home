"""Validated locale copy groups. Regional editions share an explicit base translation."""

import json

GROUPS = {
    "navigation": ["skip", "nav_apps", "nav_studio", "nav_contact", "language_label"],
    "hero": ["eyebrow", "hero_line_1", "hero_line_2", "hero_line_3", "hero_description", "hero_cta", "hero_secondary", "hero_note"],
    "motion": ["motion_label", "motion_pause", "motion_resume", "motion_reduced"],
    "story": ["story_title"],
    "learn": ["story_learn_label", "story_learn_title", "story_learn_description", "story_learn_caption"],
    "move": ["story_move_label", "story_move_title", "story_move_description", "story_move_caption"],
    "play": ["story_play_label", "story_play_title", "story_play_description", "story_play_caption"],
    "apps": ["apps_eyebrow", "apps_title", "apps_description", "visit"],
    "studio": ["studio_title", "studio_description", "studio_description_2", "studio_art_note"],
    "principles": ["principle_1_title", "principle_1_text", "principle_2_title", "principle_2_text", "principle_3_title", "principle_3_text"],
    "contact": ["contact_title", "contact_description", "contact_email", "github", "back_to_top", "footer_note"],
    "screenshot": ["screenshot_label"],
}


def load_copy(source, locale, apps):
    language = locale["code"]
    base = locale.get("copy", language)
    original = json.loads((source / "copy.json").read_text(encoding="utf-8"))
    if base in original:
        copy = original[base]
        tags = {app["id"]: app["tag"][base] for app in apps}
    else:
        path = source / "locales" / (base + ".json")
        groups = json.loads(path.read_text(encoding="utf-8"))
        if set(groups) != set(GROUPS) | {"tags"}:
            raise ValueError("Invalid translation groups: " + str(path))
        copy = {}
        for group, keys in GROUPS.items():
            values = groups[group]
            if len(values) != len(keys) or not all(isinstance(v, str) and v.strip() for v in values):
                raise ValueError("Missing translation: " + base + " / " + group)
            copy.update(zip(keys, values))
        if len(groups["tags"]) != len(apps) or not all(isinstance(v, str) and v.strip() for v in groups["tags"]):
            raise ValueError("Expected one translated category per app: " + base)
        tags = dict(zip((app["id"] for app in apps), groups["tags"]))
        copy.update({
            "title": "Ultimate Digital — " + copy["eyebrow"],
            "description": copy["studio_description"],
            "story_eyebrow": copy["hero_secondary"],
            "art_label": copy["hero_note"],
            "art_caption": copy["story_learn_label"],
            "visit_label": copy["visit"] + ":",
            "studio_eyebrow": copy["nav_studio"],
            "contact_eyebrow": copy["nav_contact"],
            "copyright": copy["eyebrow"],
        })
        localized = json.loads((source / "app-localizations.json").read_text(encoding="utf-8"))[language]
        for topic, app in [("learn", "periodic-table"), ("move", "unlocky"), ("play", "im-bored")]:
            copy["story_" + topic + "_link"] = copy["visit"] + ": " + localized[app]["name"]
            copy["story_" + topic + "_alt"] = localized[app]["name"] + " — " + copy["screenshot_label"]
        for index, topic in enumerate(["learn", "move", "play"], 1):
            copy["strip_" + str(index)] = copy["story_" + topic + "_title"].replace("\n", " ")
    # The social image is the studio's English wordmark, not translated artwork.
    copy["social_alt"] = "Ultimate Digital"
    return copy, tags
