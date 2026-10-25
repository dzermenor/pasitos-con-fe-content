#!/usr/bin/env python3
"""Validate every story (schema 2) using only Python's standard library.

Mirrors StoryContentValidator in the Android app: keep both in sync.
"""

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 2
MIN_READING_SCENES = 2
MAX_ITEMS = 6
MAX_WRONG_ITEMS = 4
# App versionCode that first shipped each mechanic. When a release adds one, add it here
# with the new versionCode: stories using it must then declare that minAppVersion.
INTERACTION_MIN_APP_VERSION = {
    "COLLECT": 1,
    "HOLD": 1,
    "SWIPE": 1,
    "TIMING": 1,
    "DELIVER": 1,
    "CHOICE": 1,
}


def read_json(path: Path):
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def safe_relative_path(value: str) -> bool:
    path = Path(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts


def valid_asset_url(value) -> bool:
    if value is None:
        return True
    if not isinstance(value, str) or not value:
        return False
    parsed = urlparse(value)
    if parsed.scheme:
        return parsed.scheme == "https" and bool(parsed.netloc)
    return safe_relative_path(value)


def validate_asset(value, label, errors):
    if not valid_asset_url(value):
        errors.append(f"{label} must be HTTPS, relative, or null")
    elif value and not urlparse(value).scheme and not (ROOT / value).is_file():
        errors.append(f"{label} points to a missing file: {value}")


def validate_collect_images(interaction, count, prefix, errors):
    item_images = interaction.get("itemImages") or []
    wrong_images = interaction.get("wrongItemImages") or []
    if isinstance(count, int) and len(item_images) > count:
        errors.append(f"{prefix}: COLLECT itemImages cannot exceed count")
    if len(wrong_images) > MAX_WRONG_ITEMS:
        errors.append(f"{prefix}: COLLECT wrongItemImages allows at most {MAX_WRONG_ITEMS}")
    # Screen reader users rely on the label to tell wrong items apart.
    if wrong_images and not interaction.get("wrongItemLabel"):
        errors.append(f"{prefix}: COLLECT wrongItemLabel is required with wrongItemImages")
    for i, image in enumerate(item_images):
        validate_asset(image, f"{prefix}.itemImages[{i}]", errors)
    for i, image in enumerate(wrong_images):
        validate_asset(image, f"{prefix}.wrongItemImages[{i}]", errors)


def validate_interaction(interaction, prefix, errors):
    if not isinstance(interaction, dict):
        errors.append(f"{prefix}: interaction must be an object")
        return
    kind = interaction.get("type")
    if kind not in INTERACTION_MIN_APP_VERSION:
        errors.append(f"{prefix}: unknown interaction type {kind!r}")
    elif kind in ("COLLECT", "DELIVER"):
        count = interaction.get("count")
        if not isinstance(count, int) or not 1 <= count <= MAX_ITEMS:
            errors.append(f"{prefix}: {kind} count must be between 1 and {MAX_ITEMS}")
        if not interaction.get("itemLabel"):
            errors.append(f"{prefix}: {kind} itemLabel is required")
        if kind == "DELIVER":
            if not interaction.get("itemImage"):
                errors.append(f"{prefix}: DELIVER itemImage is required")
            for field in ("targetLabel", "hint"):
                if not interaction.get(field):
                    errors.append(f"{prefix}: DELIVER {field} is required")
        validate_asset(interaction.get("itemImage"), f"{prefix}.itemImage", errors)
        if kind == "COLLECT":
            validate_collect_images(interaction, count, prefix, errors)
    elif kind in ("HOLD", "SWIPE"):
        if not interaction.get("hint"):
            errors.append(f"{prefix}: {kind} hint is required")
        duration = interaction.get("durationMillis")
        if kind == "HOLD" and duration is not None and not (isinstance(duration, int) and 500 <= duration <= 5000):
            errors.append(f"{prefix}: HOLD durationMillis must be between 500 and 5000")
    elif kind == "TIMING":
        if not interaction.get("hint"):
            errors.append(f"{prefix}: TIMING hint is required")
        period = interaction.get("periodMillis")
        if period is not None and not (isinstance(period, int) and 800 <= period <= 4000):
            errors.append(f"{prefix}: TIMING periodMillis must be between 800 and 4000")
        validate_asset(interaction.get("itemImage"), f"{prefix}.itemImage", errors)
    elif kind == "CHOICE":
        options = interaction.get("options") or []
        if not 2 <= len(options) <= 4:
            errors.append(f"{prefix}: CHOICE needs between 2 and 4 options")
        ids = [option.get("id") for option in options]
        if len(ids) != len(set(ids)):
            errors.append(f"{prefix}: CHOICE option ids must be unique")
        if any(not option.get("id") or not option.get("label") for option in options):
            errors.append(f"{prefix}: CHOICE options require id and label")
        # Every option needs something to say: its own response or the shared one.
        if not interaction.get("response") and any(not option.get("response") for option in options):
            errors.append(f"{prefix}: CHOICE response is required unless every option has its own response")
        correct = interaction.get("correctOptionId")
        if correct is not None and correct not in ids:
            errors.append(f"{prefix}: CHOICE correctOptionId must match an option id")


def is_activity(scene) -> bool:
    interaction = scene.get("interaction")
    return isinstance(interaction, dict) and interaction.get("type") != "CHOICE"


def validate_story(item, errors):
    path_value = item.get("path", "")
    if not safe_relative_path(path_value):
        errors.append(f"Catalog path is unsafe: {path_value!r}")
        return

    path = ROOT / path_value
    if not path.is_file():
        errors.append(f"Story file does not exist: {path_value}")
        return

    try:
        story = read_json(path)
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"Cannot read {path_value}: {error}")
        return

    label = story.get("id", path_value)
    if story.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"{label}: schemaVersion must be {SCHEMA_VERSION}")
    if story.get("id") != item.get("id"):
        errors.append(f"{label}: id does not match catalog")
    if story.get("version") != item.get("version"):
        errors.append(f"{label}: version does not match catalog")
    for field in ("title", "subtitle", "bibleReference"):
        if not story.get(field):
            errors.append(f"{label}: {field} is required")
    if story.get("estimatedMinutes") not in range(1, 31):
        errors.append(f"{label}: estimatedMinutes must be between 1 and 30")
    source = story.get("source")
    if not isinstance(source, dict):
        errors.append(f"{label}: source is required")
    else:
        for field in ("narrative", "verseTranslation", "license"):
            if not source.get(field):
                errors.append(f"{label}.source: {field} is required")
    validate_asset(story.get("coverImage"), f"{label}.coverImage", errors)

    scenes = story.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append(f"{label}: scenes must not be empty")
        return

    ids = [scene.get("id") for scene in scenes]
    if len(ids) != len(set(ids)):
        errors.append(f"{label}: scene ids must be unique")
    if scenes[0].get("interaction") is not None:
        errors.append(f"{label}: first scene must be a cover without interaction")
    last_interaction = scenes[-1].get("interaction") or {}
    if last_interaction.get("type") != "CHOICE":
        errors.append(f"{label}: last scene must be a CHOICE reflection")

    first_activity = next((index for index, scene in enumerate(scenes) if is_activity(scene)), None)
    if first_activity is not None:
        reading = sum(scene.get("interaction") is None for scene in scenes[1:first_activity])
        if reading < MIN_READING_SCENES:
            errors.append(f"{label}: at least two reading scenes must precede interactions")

    for index, scene in enumerate(scenes):
        prefix = f"{label}.scenes[{index}]"
        for field in ("id", "title"):
            if not scene.get(field):
                errors.append(f"{prefix}: {field} is required")
        verse = scene.get("verse")
        if verse is not None and (not verse.get("text") or not verse.get("reference")):
            errors.append(f"{prefix}: verse text and reference are required")
        validate_asset(scene.get("image"), f"{prefix}.image", errors)
        if scene.get("interaction") is not None:
            validate_interaction(scene["interaction"], prefix, errors)

    # Older apps reject unknown mechanics, so the catalog must keep the story away from them.
    kinds = {scene["interaction"].get("type") for scene in scenes if isinstance(scene.get("interaction"), dict)}
    required = max((INTERACTION_MIN_APP_VERSION.get(kind, 1) for kind in kinds), default=1)
    declared = item.get("minAppVersion", 1)
    if isinstance(declared, int) and 1 <= declared < required:
        errors.append(f"{label}: catalog minAppVersion must be at least {required} for the mechanics it uses")


def main() -> int:
    errors = []
    try:
        catalog = read_json(ROOT / "catalog.json")
    except (OSError, json.JSONDecodeError) as error:
        print(f"Cannot read catalog.json: {error}", file=sys.stderr)
        return 1

    if catalog.get("schemaVersion") != 1:
        errors.append("catalog.schemaVersion must be 1")
    stories = catalog.get("stories")
    if not isinstance(stories, list):
        errors.append("catalog.stories must be an array")
        stories = []
    catalog_ids = [item.get("id") for item in stories]
    if len(catalog_ids) != len(set(catalog_ids)):
        errors.append("catalog story ids must be unique")

    for item in stories:
        if not item.get("id"):
            errors.append("catalog story id is required")
        if not isinstance(item.get("version"), int) or item.get("version", 0) < 1:
            errors.append(f"catalog item {item.get('id')!r}: version must be at least 1")
        min_app = item.get("minAppVersion", 1)
        if not isinstance(min_app, int) or isinstance(min_app, bool) or min_app < 1:
            errors.append(f"catalog item {item.get('id')!r}: minAppVersion must be an integer of at least 1")
        validate_story(item, errors)

    if errors:
        print("Content validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Content valid: {len(stories)} story/stories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
