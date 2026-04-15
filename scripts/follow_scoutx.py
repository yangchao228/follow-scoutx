#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from typing import Any
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_FEED_URL = "http://192.144.134.94:9100/v1/public/feed"
DEFAULT_X_FEED_URL = "https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-x.json"
DEFAULT_PODCAST_FEED_URL = "https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-podcasts.json"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_USER_AGENT = "FollowScoutXSkill/0.1 (+https://input.reai.group)"
PROFILE_VERSION = 1
DEFAULT_SUMMARY_BUDGET_CHARS = 1200
SOURCE_TYPES = ("scoutx", "x", "podcast")
SOURCE_TYPE_LABELS = {
    "scoutx": "ScoutX",
    "x": "X",
    "podcast": "Podcast",
}
SOURCE_TYPE_ENV_VARS = {
    "scoutx": "FOLLOW_SCOUTX_FEED_URL",
    "x": "FOLLOW_SCOUTX_X_FEED_URL",
    "podcast": "FOLLOW_SCOUTX_PODCAST_FEED_URL",
}
SOURCE_MODE_TO_TYPES = {
    "scoutx": ["scoutx"],
    "curated": ["scoutx"],
    "media": ["scoutx"],
    "first_party": ["x", "podcast"],
    "first-party": ["x", "podcast"],
    "primary": ["x", "podcast"],
    "mixed": ["scoutx", "x", "podcast"],
    "all": ["scoutx", "x", "podcast"],
}
SOURCE_TYPE_ALIASES = {
    "scoutx": "scoutx",
    "media": "scoutx",
    "curated": "scoutx",
    "x": "x",
    "twitter": "x",
    "tweet": "x",
    "tweets": "x",
    "podcast": "podcast",
    "podcasts": "podcast",
    "播客": "podcast",
}
MESSAGE_GROUPS = {
    "first_party": ("x", "podcast"),
    "scoutx": ("scoutx",),
}
MESSAGE_GROUP_ORDER = ("first_party", "scoutx")
MESSAGE_GROUP_CHOICES = ("all", "first_party", "scoutx")
MESSAGE_GROUP_LIMIT_KEYS = {
    "first_party": "max_first_party_items",
    "scoutx": "max_scoutx_items",
}
MESSAGE_GROUP_NAME_SUFFIXES = {
    "first_party": "first-party",
    "scoutx": "scoutx",
}
STYLE_TO_SUMMARY_BUDGET = {
    "short": 700,
    "medium": 900,
    "long": 1200,
}
STYLE_TO_ITEM_TIMEOUT_SECONDS = {
    "short": 45,
    "medium": 60,
    "long": 90,
}
DAY_TO_CRON = {
    "sun": "0",
    "mon": "1",
    "tue": "2",
    "wed": "3",
    "thu": "4",
    "fri": "5",
    "sat": "6",
}


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def current_script_path() -> str:
    return str(Path(__file__).resolve())


def user_home() -> Path:
    override = os.getenv("FOLLOW_SCOUTX_HOME", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".follow_scoutx"


def profile_path() -> Path:
    return user_home() / "profile.json"


def state_path() -> Path:
    return user_home() / "state.json"


def local_service_config_path() -> Path:
    return user_home() / "service.json"


def prompts_dir() -> Path:
    return user_home() / "prompts"


def bundled_prompts_dir() -> Path:
    return skill_root() / "prompts"


def service_config_path() -> Path:
    return skill_root() / "service.json"


def default_service_config() -> dict[str, Any]:
    return {
        "feed_url": DEFAULT_FEED_URL,
        "scoutx_feed_url": DEFAULT_FEED_URL,
        "x_feed_url": DEFAULT_X_FEED_URL,
        "podcast_feed_url": DEFAULT_PODCAST_FEED_URL,
        "meta_url": "",
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
    }


def with_service_defaults(config: dict[str, Any]) -> dict[str, Any]:
    merged = default_service_config()
    merged.update(config)
    scoutx_feed_url = str(merged.get("scoutx_feed_url") or merged.get("feed_url") or DEFAULT_FEED_URL)
    merged["feed_url"] = str(merged.get("feed_url") or scoutx_feed_url)
    merged["scoutx_feed_url"] = scoutx_feed_url
    merged["x_feed_url"] = str(merged.get("x_feed_url") or DEFAULT_X_FEED_URL)
    merged["podcast_feed_url"] = str(merged.get("podcast_feed_url") or DEFAULT_PODCAST_FEED_URL)
    merged["timeout_seconds"] = int(merged.get("timeout_seconds") or DEFAULT_TIMEOUT_SECONDS)
    return merged


def load_service_config() -> dict[str, Any]:
    local_path = local_service_config_path()
    if local_path.exists():
        return with_service_defaults(json.loads(local_path.read_text(encoding="utf-8")))

    bundled_path = service_config_path()
    if bundled_path.exists():
        return with_service_defaults(json.loads(bundled_path.read_text(encoding="utf-8")))

    return default_service_config()


def is_placeholder_feed_url(url: str | None) -> bool:
    if not url:
        return True
    parsed = urllib.parse.urlparse(url)
    host = (parsed.netloc or "").lower()
    return host.endswith(".example.com") or host == "example.com"


def ensure_real_feed_url(url: str | None) -> str:
    if is_placeholder_feed_url(url):
        raise SystemExit(
            "Follow ScoutX operator setup incomplete: the bundled feed URL is still a placeholder. "
            "Update the distributed skill package's service.json or run configure-service on this installation. "
            "Normal end users should not be asked to provide a feed URL."
        )
    return str(url)


def save_service_config(config: dict[str, Any]) -> None:
    save_json(local_service_config_path(), config)


def default_profile() -> dict[str, Any]:
    now = utcnow_iso()
    return {
        "version": PROFILE_VERSION,
        "created_at": now,
        "updated_at": now,
        "schedule": {
            "frequency": "daily",
            "time": "09:00",
            "days": ["mon"],
        },
        "delivery": {
            "channel": "in_chat",
            "target": "",
        },
        "preferences": {
            "language": "zh-CN",
            "source_mode": "scoutx",
            "source_types": ["scoutx"],
            "topics": [],
            "keywords_include": [],
            "keywords_exclude": [],
            "preferred_sources": [],
            "max_items": 8,
            "max_first_party_items": None,
            "max_scoutx_items": None,
        },
        "style": {
            "length": "short",
            "tone": "clear",
        },
    }


def default_state() -> dict[str, Any]:
    return {
        "last_preview_at": None,
        "last_feed_fetch_at": None,
        "last_digest_item_ids": [],
    }


def load_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return json.loads(json.dumps(fallback))
    return json.loads(path.read_text(encoding="utf-8"))


def merge_missing_defaults(payload: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    for key, value in defaults.items():
        if key not in payload:
            payload[key] = json.loads(json.dumps(value))
            continue
        if isinstance(payload[key], dict) and isinstance(value, dict):
            merge_missing_defaults(payload[key], value)
    return payload


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_local_files() -> None:
    home = user_home()
    home.mkdir(parents=True, exist_ok=True)
    prompts_dir().mkdir(parents=True, exist_ok=True)

    if not profile_path().exists():
        save_json(profile_path(), default_profile())
    if not state_path().exists():
        save_json(state_path(), default_state())
    if not local_service_config_path().exists():
        save_service_config(load_service_config())

    for source in bundled_prompts_dir().glob("*.md"):
        target = prompts_dir() / source.name
        if not target.exists():
            shutil.copyfile(source, target)


def load_profile() -> dict[str, Any]:
    ensure_local_files()
    profile = load_json(profile_path(), default_profile())
    return merge_missing_defaults(profile, default_profile())


def save_profile(profile: dict[str, Any]) -> None:
    profile["version"] = PROFILE_VERSION
    profile["updated_at"] = utcnow_iso()
    save_json(profile_path(), profile)


def load_state() -> dict[str, Any]:
    ensure_local_files()
    return load_json(state_path(), default_state())


def save_state(state: dict[str, Any]) -> None:
    save_json(state_path(), state)


def load_prompt_texts() -> dict[str, str]:
    ensure_local_files()
    mapping = {
        "digest_intro": "digest_intro.md",
        "summarize_content": "summarize_content.md",
        "summarize_tweets": "summarize_tweets.md",
        "summarize_podcast": "summarize_podcast.md",
        "translate": "translate.md",
    }
    prompts: dict[str, str] = {}
    for key, filename in mapping.items():
        prompt_path = prompts_dir() / filename
        prompts[key] = prompt_path.read_text(encoding="utf-8").strip()
    return prompts


def split_csv(value: str | None) -> list[str] | None:
    if value is None:
        return None
    items = [part.strip() for part in value.split(",")]
    return [item for item in items if item]


def normalize_source_type(value: str) -> str | None:
    key = value.strip().lower().replace("-", "_")
    if key in SOURCE_TYPE_ALIASES:
        return SOURCE_TYPE_ALIASES[key]
    if key == "first_party":
        return None
    return key if key in SOURCE_TYPES else None


def normalize_source_types(values: list[str] | None, *, strict: bool = False) -> list[str]:
    if not values:
        return ["scoutx"]
    normalized: list[str] = []
    invalid: list[str] = []
    for value in values:
        source_type = normalize_source_type(value)
        if source_type and source_type not in normalized:
            normalized.append(source_type)
        elif not source_type:
            invalid.append(value)
    if invalid and strict:
        expected = ", ".join(SOURCE_TYPES)
        invalid_text = ", ".join(invalid)
        raise ValueError(f"Unknown source type(s): {invalid_text}. Expected one of: {expected}.")
    return normalized or ["scoutx"]


def source_types_for_mode(mode: str | None) -> list[str]:
    if not mode:
        return ["scoutx"]
    key = mode.strip().lower().replace(" ", "_")
    return list(SOURCE_MODE_TO_TYPES.get(key, ["scoutx"]))


def profile_source_types(profile: dict[str, Any]) -> list[str]:
    preferences = profile.get("preferences") or {}
    configured = preferences.get("source_types")
    if configured:
        return normalize_source_types([str(value) for value in configured])
    return source_types_for_mode(str(preferences.get("source_mode") or "scoutx"))


def selected_message_group_ids(profile: dict[str, Any], message_group: str | None = "all") -> list[str]:
    selected_sources = set(profile_source_types(profile))
    group_ids = [
        group_id
        for group_id in MESSAGE_GROUP_ORDER
        if any(source_type in selected_sources for source_type in MESSAGE_GROUPS[group_id])
    ]
    if message_group and message_group != "all":
        return [group_id for group_id in group_ids if group_id == message_group]
    return group_ids


def source_types_for_message_group(profile: dict[str, Any], message_group: str | None = "all") -> list[str]:
    selected_sources = profile_source_types(profile)
    if not message_group or message_group == "all":
        return selected_sources
    allowed_sources = set(MESSAGE_GROUPS.get(message_group, ()))
    return [source_type for source_type in selected_sources if source_type in allowed_sources]


def group_limit_key(group_id: str) -> str:
    return MESSAGE_GROUP_LIMIT_KEYS[group_id]


def configured_group_limits(profile: dict[str, Any]) -> dict[str, int]:
    preferences = profile.get("preferences") or {}
    group_ids = selected_message_group_ids(profile, "all")
    if not group_ids:
        return {}

    total_limit = max(0, int(preferences.get("max_items", 8) or 0))
    base_limit = total_limit // len(group_ids)
    remainder = total_limit % len(group_ids)
    limits = {
        group_id: base_limit + (1 if index < remainder else 0)
        for index, group_id in enumerate(group_ids)
    }

    for group_id in group_ids:
        key = group_limit_key(group_id)
        explicit_limit = preferences.get(key)
        if explicit_limit is not None:
            limits[group_id] = max(0, int(explicit_limit))
    return limits


def message_group_label(group_id: str, language: str) -> str:
    if group_id == "first_party":
        if language == "en":
            return "First-party Sources (X / Podcasts)"
        if language == "bilingual":
            return "First-party Sources / 一手信息源（X 平台 / 播客）"
        return "一手信息源（X 平台 / 播客）"
    if language == "en":
        return "ScoutX Curated Media"
    if language == "bilingual":
        return "ScoutX Curated Media / ScoutX 优质自媒体信息源"
    return "ScoutX 优质自媒体信息源"


def update_profile_from_args(profile: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if args.frequency:
        profile["schedule"]["frequency"] = args.frequency
    if args.time:
        profile["schedule"]["time"] = args.time
    if args.days is not None:
        profile["schedule"]["days"] = split_csv(args.days) or []

    if args.language:
        profile["preferences"]["language"] = args.language
    if args.source_mode:
        source_types = source_types_for_mode(args.source_mode)
        profile["preferences"]["source_mode"] = args.source_mode
        profile["preferences"]["source_types"] = source_types
    if args.source_types is not None:
        try:
            source_types = normalize_source_types(split_csv(args.source_types) or [], strict=True)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        profile["preferences"]["source_types"] = source_types
        if source_types == ["scoutx"]:
            profile["preferences"]["source_mode"] = "scoutx"
        elif source_types == ["x", "podcast"]:
            profile["preferences"]["source_mode"] = "first_party"
        elif source_types == ["scoutx", "x", "podcast"]:
            profile["preferences"]["source_mode"] = "mixed"
        else:
            profile["preferences"]["source_mode"] = "custom"
    if args.topics is not None:
        profile["preferences"]["topics"] = split_csv(args.topics) or []
    if args.keywords_include is not None:
        profile["preferences"]["keywords_include"] = split_csv(args.keywords_include) or []
    if args.keywords_exclude is not None:
        profile["preferences"]["keywords_exclude"] = split_csv(args.keywords_exclude) or []
    if args.preferred_sources is not None:
        profile["preferences"]["preferred_sources"] = split_csv(args.preferred_sources) or []
    if args.max_items is not None:
        profile["preferences"]["max_items"] = args.max_items
    if arg_value(args, "max_first_party_items") is not None:
        profile["preferences"]["max_first_party_items"] = args.max_first_party_items
    if arg_value(args, "max_scoutx_items") is not None:
        profile["preferences"]["max_scoutx_items"] = args.max_scoutx_items

    if args.delivery_channel:
        profile["delivery"]["channel"] = args.delivery_channel
    if args.delivery_target is not None:
        profile["delivery"]["target"] = args.delivery_target

    if args.length:
        profile["style"]["length"] = args.length
    if args.tone:
        profile["style"]["tone"] = args.tone

    return profile


def summary_char_budget(profile: dict[str, Any]) -> int:
    style = str(profile.get("style", {}).get("length") or "medium").strip().lower()
    return STYLE_TO_SUMMARY_BUDGET.get(style, DEFAULT_SUMMARY_BUDGET_CHARS)


def item_timeout_seconds(profile: dict[str, Any]) -> int:
    style = str(profile.get("style", {}).get("length") or "medium").strip().lower()
    return STYLE_TO_ITEM_TIMEOUT_SECONDS.get(style, 60)


def normalize_feed_item(raw: dict[str, Any]) -> dict[str, Any]:
    source_values = raw.get("sources") or []
    sources = [str(value).strip() for value in source_values if str(value).strip()]
    return {
        "content_id": str(raw.get("content_id") or raw.get("id") or raw.get("url") or "").strip(),
        "source_type": "scoutx",
        "source_label": SOURCE_TYPE_LABELS["scoutx"],
        "title": html.unescape(str(raw.get("title") or "").strip()),
        "summary": str(raw.get("summary") or raw.get("summary_text") or raw.get("description") or raw.get("content") or "").strip(),
        "url": str(raw.get("url") or raw.get("canonical_url") or "").strip(),
        "published_at": str(raw.get("published_at") or raw.get("publishedAt") or "").strip(),
        "sources": sources or [SOURCE_TYPE_LABELS["scoutx"]],
        "tags": [str(value).strip() for value in raw.get("tags") or [] if str(value).strip()],
        "metadata": {},
    }


def normalize_x_feed_items(feed_payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for account in feed_payload.get("x") or []:
        name = str(account.get("name") or account.get("handle") or "Unknown").strip()
        handle = str(account.get("handle") or "").strip()
        for tweet in account.get("tweets") or []:
            tweet_id = str(tweet.get("id") or tweet.get("url") or "").strip()
            text = str(tweet.get("text") or "").strip()
            if not text:
                continue
            title_prefix = f"@{handle}" if handle else name
            title = f"{title_prefix}: {text.splitlines()[0][:120]}"
            items.append(
                {
                    "content_id": f"x:{tweet_id}" if tweet_id else f"x:{handle}:{tweet.get('createdAt') or tweet.get('url')}",
                    "source_type": "x",
                    "source_label": SOURCE_TYPE_LABELS["x"],
                    "title": title,
                    "summary": text,
                    "url": str(tweet.get("url") or "").strip(),
                    "published_at": str(tweet.get("createdAt") or tweet.get("published_at") or "").strip(),
                    "sources": [f"X / {name}", f"@{handle}" if handle else name],
                    "tags": ["x"],
                    "metadata": {
                        "name": name,
                        "handle": handle,
                        "likes": tweet.get("likes"),
                        "retweets": tweet.get("retweets"),
                        "replies": tweet.get("replies"),
                        "is_quote": tweet.get("isQuote"),
                    },
                }
            )
    return items


def normalize_podcast_feed_items(feed_payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for episode in feed_payload.get("podcasts") or []:
        name = str(episode.get("name") or "Unknown Podcast").strip()
        title = html.unescape(str(episode.get("title") or "Untitled podcast episode").strip())
        content = str(
            episode.get("transcript")
            or episode.get("content")
            or episode.get("summary")
            or episode.get("description")
            or ""
        ).strip()
        items.append(
            {
                "content_id": f"podcast:{episode.get('guid') or episode.get('url') or title}",
                "source_type": "podcast",
                "source_label": SOURCE_TYPE_LABELS["podcast"],
                "title": title,
                "summary": content,
                "url": str(episode.get("url") or "").strip(),
                "published_at": str(episode.get("publishedAt") or episode.get("published_at") or "").strip(),
                "sources": [f"Podcast / {name}"],
                "tags": ["podcast"],
                "metadata": {
                    "name": name,
                    "guid": episode.get("guid"),
                },
            }
        )
    return items


def normalize_items_for_source(source_type: str, feed_payload: dict[str, Any]) -> list[dict[str, Any]]:
    if source_type == "x":
        return normalize_x_feed_items(feed_payload)
    if source_type == "podcast":
        return normalize_podcast_feed_items(feed_payload)
    return [normalize_feed_item(item) for item in feed_payload.get("items") or []]


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_paragraphs(text: str) -> list[str]:
    normalized = normalize_whitespace(text)
    if not normalized:
        return []
    return [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]


def split_sentences(text: str) -> list[str]:
    normalized = normalize_whitespace(text)
    if not normalized:
        return []
    parts = re.split(r"(?<=[。！？!?；;])\s*", normalized)
    return [part.strip() for part in parts if part.strip()]


def strip_trailing_noise(paragraphs: list[str]) -> list[str]:
    noise_patterns = [
        "本文来自",
        "参考资料",
        "责任编辑",
        "编辑：",
        "作者：",
        "文章来源",
    ]
    cleaned = list(paragraphs)
    while cleaned and any(pattern in cleaned[-1] for pattern in noise_patterns):
        cleaned.pop()
    return cleaned


def dedupe_sentences(sentences: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for sentence in sentences:
        key = re.sub(r"\s+", "", sentence)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(sentence)
    return deduped


def sentence_priority(sentence: str) -> int:
    keywords = [
        "因此",
        "所以",
        "综上",
        "总之",
        "最终",
        "结论是",
        "认为",
        "指出",
        "提出",
        "强调",
        "观点是",
        "数据显示",
        "结果表明",
        "研究发现",
        "超过",
        "增长到",
        "关键",
        "重要",
        "核心",
        "值得注意的是",
    ]
    score = 0
    for keyword in keywords:
        if keyword in sentence:
            score += 2
    if re.search(r"\d", sentence):
        score += 1
    if re.search(r"%|亿美元|万亿|million|billion|stars?|GPU|API|Beta|Alpha", sentence, re.IGNORECASE):
        score += 1
    return score


def compress_summary_text(text: str, *, char_budget: int = DEFAULT_SUMMARY_BUDGET_CHARS) -> str:
    paragraphs = strip_trailing_noise(split_paragraphs(text))
    if not paragraphs:
        return ""

    if len("".join(paragraphs)) <= char_budget:
        return "\n\n".join(paragraphs)

    first_paragraph = paragraphs[0]
    last_paragraph = paragraphs[-1] if len(paragraphs) > 1 else ""
    middle_paragraphs = paragraphs[1:-1] if len(paragraphs) > 2 else []

    middle_sentences = dedupe_sentences(
        [sentence for paragraph in middle_paragraphs for sentence in split_sentences(paragraph)]
    )
    selected_middle = [sentence for sentence in middle_sentences if sentence_priority(sentence) > 0]
    if not selected_middle:
        selected_middle = middle_sentences[:8]

    assembled_parts: list[str] = [first_paragraph]
    if selected_middle:
        assembled_parts.append(" ".join(selected_middle))
    if last_paragraph and last_paragraph != first_paragraph:
        assembled_parts.append(last_paragraph)

    result = "\n\n".join(part for part in assembled_parts if part).strip()
    if len(result) <= char_budget:
        return result

    parts = [first_paragraph]
    if last_paragraph and last_paragraph != first_paragraph:
        remaining_budget = max(char_budget - len(first_paragraph) - len(last_paragraph) - 4, 0)
    else:
        remaining_budget = max(char_budget - len(first_paragraph) - 2, 0)

    if remaining_budget > 0 and selected_middle:
        middle_text = ""
        for sentence in selected_middle:
            candidate = f"{middle_text} {sentence}".strip()
            if len(candidate) > remaining_budget:
                break
            middle_text = candidate
        if middle_text:
            parts.append(middle_text)

    if last_paragraph and last_paragraph != first_paragraph:
        parts.append(last_paragraph)

    result = "\n\n".join(part for part in parts if part).strip()
    if len(result) <= char_budget:
        return result

    return result[:char_budget].rstrip()


def compress_transcript_text(text: str, *, char_budget: int = DEFAULT_SUMMARY_BUDGET_CHARS) -> str:
    paragraphs = split_paragraphs(text)
    if not paragraphs:
        return ""
    selected: list[str] = []
    current_len = 0
    for paragraph in paragraphs:
        candidate_len = current_len + len(paragraph) + (2 if selected else 0)
        if candidate_len > char_budget:
            remaining = char_budget - current_len - (2 if selected else 0)
            if remaining > 80:
                selected.append(paragraph[:remaining].rstrip())
            break
        selected.append(paragraph)
        current_len = candidate_len
    return "\n\n".join(selected).strip()


def compress_item_summary(item: dict[str, Any], *, char_budget: int = DEFAULT_SUMMARY_BUDGET_CHARS) -> str:
    summary = str(item.get("summary") or "")
    if item.get("source_type") == "podcast":
        return compress_transcript_text(summary, char_budget=char_budget)
    return compress_summary_text(summary, char_budget=char_budget)


def item_text(item: dict[str, Any]) -> str:
    return "\n".join(
        [
            str(item.get("title") or ""),
            str(item.get("summary") or ""),
            str(item.get("source_type") or ""),
            str(item.get("source_label") or ""),
            " ".join(item["sources"]),
            " ".join(item["tags"]),
        ]
    ).lower()


def item_matches_profile(item: dict[str, Any], profile: dict[str, Any]) -> bool:
    preferences = profile["preferences"]
    include_terms = [value.lower() for value in preferences.get("topics", []) + preferences.get("keywords_include", [])]
    exclude_terms = [value.lower() for value in preferences.get("keywords_exclude", [])]
    preferred_sources = {value.lower() for value in preferences.get("preferred_sources", [])}
    item_sources = {value.lower() for value in item.get("sources", [])}
    haystack = item_text(item)

    if preferred_sources and not (preferred_sources & item_sources):
        return False
    if include_terms and not any(term in haystack for term in include_terms):
        return False
    if exclude_terms and any(term in haystack for term in exclude_terms):
        return False
    return True


def service_feed_url(service_config: dict[str, Any], source_type: str) -> str:
    if source_type == "x":
        return str(service_config.get("x_feed_url") or DEFAULT_X_FEED_URL)
    if source_type == "podcast":
        return str(service_config.get("podcast_feed_url") or DEFAULT_PODCAST_FEED_URL)
    return str(service_config.get("scoutx_feed_url") or service_config.get("feed_url") or DEFAULT_FEED_URL)


def fetch_feed(
    *,
    source_type: str = "scoutx",
    feed_url: str | None = None,
    feed_file: str | None = None,
) -> dict[str, Any]:
    if feed_file:
        return json.loads(Path(feed_file).read_text(encoding="utf-8"))

    service_config = load_service_config()
    env_var = SOURCE_TYPE_ENV_VARS.get(source_type, "FOLLOW_SCOUTX_FEED_URL")
    target_url = feed_url or os.getenv(env_var, service_feed_url(service_config, source_type))
    target_url = ensure_real_feed_url(target_url)
    timeout = int(
        os.getenv(
            "FOLLOW_SCOUTX_TIMEOUT_SECONDS",
            str(service_config.get("timeout_seconds") or DEFAULT_TIMEOUT_SECONDS),
        )
    )
    request = urllib.request.Request(
        url=target_url,
        headers={
            "Accept": "application/json",
            "User-Agent": os.getenv("FOLLOW_SCOUTX_USER_AGENT", DEFAULT_USER_AGENT),
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} {exc.reason}: {body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to fetch central feed: {exc.reason}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Central feed returned invalid JSON: {raw}") from exc


def arg_value(args: argparse.Namespace, name: str) -> Any:
    return getattr(args, name, None)


def fetch_selected_feed_payload(profile: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    message_group = arg_value(args, "message_group") or "all"
    source_types = source_types_for_message_group(profile, message_group)
    feeds: dict[str, Any] = {}
    errors: list[str] = []

    if not source_types:
        raise SystemExit(f"No sources are selected for message group: {message_group}.")

    for source_type in source_types:
        feed_url = arg_value(args, "feed_url") if source_type == "scoutx" else arg_value(args, f"{source_type}_feed_url")
        feed_file = arg_value(args, "feed_file") if source_type == "scoutx" else arg_value(args, f"{source_type}_feed_file")
        if arg_value(args, "feed_file") and len(source_types) == 1 and not feed_file:
            feed_file = arg_value(args, "feed_file")
        try:
            feeds[source_type] = fetch_feed(source_type=source_type, feed_url=feed_url, feed_file=feed_file)
        except (SystemExit, OSError, json.JSONDecodeError) as exc:
            errors.append(f"{source_type}: {exc}")

    if not feeds:
        raise SystemExit("; ".join(errors) or "No selected feeds could be loaded.")

    generated_at = utcnow_iso()
    for payload in feeds.values():
        generated_at = str(payload.get("generated_at") or payload.get("generatedAt") or generated_at)
        if generated_at:
            break

    return {
        "generated_at": generated_at,
        "source_types": source_types,
        "feeds": feeds,
        "errors": errors,
    }


def limit_items_by_source(items: list[dict[str, Any]], source_types: list[str], limit: int) -> list[dict[str, Any]]:
    if len(source_types) <= 1:
        return items[:limit]

    buckets = {
        source_type: [item for item in items if item.get("source_type") == source_type]
        for source_type in source_types
    }
    selected: list[dict[str, Any]] = []
    index = 0
    while len(selected) < limit:
        added = False
        for source_type in source_types:
            bucket = buckets.get(source_type) or []
            if index < len(bucket):
                selected.append(bucket[index])
                added = True
                if len(selected) >= limit:
                    break
        if not added:
            break
        index += 1
    return selected


def normalize_feed_payload_items(profile: dict[str, Any], feed_payload: dict[str, Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    if "feeds" in feed_payload:
        for source_type in feed_payload.get("source_types") or profile_source_types(profile):
            normalized.extend(normalize_items_for_source(source_type, feed_payload.get("feeds", {}).get(source_type) or {}))
    else:
        source_types = profile_source_types(profile)
        if "x" in feed_payload and "x" in source_types:
            normalized.extend(normalize_items_for_source("x", feed_payload))
        if "podcasts" in feed_payload and "podcast" in source_types:
            normalized.extend(normalize_items_for_source("podcast", feed_payload))
        if "items" in feed_payload and "scoutx" in source_types:
            normalized.extend(normalize_items_for_source("scoutx", feed_payload))
    return normalized


def build_digest_groups(
    profile: dict[str, Any],
    feed_payload: dict[str, Any],
    *,
    message_group: str | None = "all",
) -> list[dict[str, Any]]:
    normalized = normalize_feed_payload_items(profile, feed_payload)
    matched = [item for item in normalized if item_matches_profile(item, profile)]
    limits = configured_group_limits(profile)
    groups: list[dict[str, Any]] = []

    for group_id in selected_message_group_ids(profile, message_group):
        group_source_types = [
            source_type
            for source_type in MESSAGE_GROUPS[group_id]
            if source_type in profile_source_types(profile)
        ]
        group_limit = limits.get(group_id, 0)
        group_items = [
            item
            for item in matched
            if item.get("source_type") in group_source_types
        ]
        groups.append(
            {
                "group_id": group_id,
                "label": message_group_label(group_id, profile["preferences"].get("language", "zh-CN")),
                "source_types": group_source_types,
                "limit": group_limit,
                "items": limit_items_by_source(group_items, group_source_types, group_limit) if group_limit > 0 else [],
            }
        )
    return groups


def flatten_digest_groups(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for group in groups for item in group.get("items", [])]


def build_preview_items(
    profile: dict[str, Any],
    feed_payload: dict[str, Any],
    *,
    message_group: str | None = "all",
) -> list[dict[str, Any]]:
    return flatten_digest_groups(build_digest_groups(profile, feed_payload, message_group=message_group))


def digest_copy(language: str) -> dict[str, str]:
    if language == "zh-CN":
        return {
            "title": "Follow ScoutX 摘要",
            "empty": "No matching items found.",
            "generated_at": "Generated at",
            "items": "Items",
            "source": "Source",
            "published": "Published",
            "link": "Link",
        }
    if language == "bilingual":
        return {
            "title": "Follow ScoutX Digest / 摘要",
            "empty": "No matching items found.",
            "generated_at": "Generated at",
            "items": "Items",
            "source": "Source",
            "published": "Published",
            "link": "Link",
        }
    return {
        "title": "Follow ScoutX Digest",
        "empty": "No matching items found.",
        "generated_at": "Generated at",
        "items": "Items",
        "source": "Source",
        "published": "Published",
        "link": "Link",
    }


def render_digest(
    profile: dict[str, Any],
    items: list[dict[str, Any]],
    generated_at: str,
    *,
    group_id: str | None = None,
) -> str:
    language = profile["preferences"].get("language", "zh-CN")
    copy = digest_copy(language)
    title = copy["title"]
    if group_id:
        title = f"{title}｜{message_group_label(group_id, language)}"
    per_item_budget = summary_char_budget(profile)
    lines = [
        title,
        "",
        f"{copy['generated_at']}: {generated_at}",
        f"{copy['items']}: {len(items)}",
        "",
    ]
    if not items:
        lines.append(copy["empty"])
        return "\n".join(lines).strip() + "\n"

    for index, item in enumerate(items, start=1):
        source = item["sources"][0] if item["sources"] else "unknown"
        lines.append(f"{index}. {item['title']}")
        summary = compress_item_summary(item, char_budget=per_item_budget) if item["summary"] else ""
        if summary:
            lines.append(summary)
        lines.append(f"{copy['source']}: {source}")
        if item["published_at"]:
            lines.append(f"{copy['published']}: {item['published_at']}")
        if item["url"]:
            lines.append(f"{copy['link']}: {item['url']}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_digest_groups(profile: dict[str, Any], groups: list[dict[str, Any]], generated_at: str) -> str:
    rendered = [
        render_digest(profile, group.get("items", []), generated_at, group_id=str(group.get("group_id") or ""))
        for group in groups
    ]
    return "\n---\n\n".join(part.strip() for part in rendered if part.strip()) + "\n"


def build_prepare_digest_payload(
    profile: dict[str, Any],
    feed_payload: dict[str, Any],
    groups: list[dict[str, Any]],
) -> dict[str, Any]:
    generated_at = str(feed_payload.get("generated_at") or utcnow_iso())
    per_item_budget = summary_char_budget(profile)
    per_item_timeout = item_timeout_seconds(profile)
    items = flatten_digest_groups(groups)

    def payload_item(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "content_id": item["content_id"],
            "source_type": item.get("source_type", "scoutx"),
            "source_label": item.get("source_label", SOURCE_TYPE_LABELS["scoutx"]),
            "title": item["title"],
            "summary_text": compress_item_summary(item, char_budget=per_item_budget),
            "canonical_url": item["url"],
            "published_at": item["published_at"],
            "sources": item["sources"],
            "tags": item["tags"],
            "metadata": item.get("metadata", {}),
        }

    return {
        "status": "ok",
        "generated_at": generated_at,
        "config": {
            "language": profile["preferences"].get("language", "zh-CN"),
            "style": profile.get("style", {}),
            "schedule": profile.get("schedule", {}),
            "preferences": {
                "source_mode": profile["preferences"].get("source_mode", "scoutx"),
                "source_types": profile_source_types(profile),
                "topics": profile["preferences"].get("topics", []),
                "keywords_include": profile["preferences"].get("keywords_include", []),
                "keywords_exclude": profile["preferences"].get("keywords_exclude", []),
                "preferred_sources": profile["preferences"].get("preferred_sources", []),
                "max_items": profile["preferences"].get("max_items", 8),
                "max_first_party_items": profile["preferences"].get("max_first_party_items"),
                "max_scoutx_items": profile["preferences"].get("max_scoutx_items"),
            },
        },
        "stats": {
            "item_count": len(items),
            "message_count": len(groups),
            "group_counts": {
                str(group.get("group_id")): len(group.get("items", []))
                for group in groups
            },
            "group_limits": {
                str(group.get("group_id")): group.get("limit", 0)
                for group in groups
            },
            "source_counts": {
                source_type: len([item for item in items if item.get("source_type") == source_type])
                for source_type in SOURCE_TYPES
            },
            "feed_generated_at": generated_at,
        },
        "processing": {
            "per_item_input_char_budget": per_item_budget,
            "per_item_timeout_seconds": per_item_timeout,
            "mode": "item_by_item",
        },
        "output_contract": {
            "title": digest_copy(profile["preferences"].get("language", "zh-CN"))["title"],
            "header_lines": [
                "Generated at: <feed generated time>",
                "Items: <number of selected items>",
            ],
            "item_template": [
                "<index>. <title>",
                "<one compact but complete paragraph based only on the item's summary_text>",
                "Source: <primary source>",
                "Published: <published_at if present>",
                "Link: <canonical_url>",
            ],
            "failure_template": [
                "<index>. <title>",
                "Status: failed",
                "Reason: <why the item could not be fully generated within the allowed budget or timeout>",
                "Source: <primary source>",
                "Published: <published_at if present>",
                "Link: <canonical_url>",
            ],
            "rules": [
                "Use only the selected items in this payload.",
                "If groups contains more than one group, produce one separate digest message per group.",
                "The first_party group covers X posts and podcasts; the scoutx group covers ScoutX curated media.",
                "Do not invent facts beyond title, summary_text, source, published_at, and canonical_url.",
                "Respect item.source_type: scoutx is the curated ScoutX media feed, x is first-party X posts, and podcast is first-party podcast transcript content.",
                "Process items one by one, not all at once.",
                "Treat processing.per_item_timeout_seconds as the maximum target time for each item.",
                "If an item cannot be fully produced within the allowed budget or timeout, emit the failure_template for that item instead of skipping it.",
                "Do not silently drop items.",
                "Keep one numbered section per item.",
                "Do not rewrite into bullet-point highlights under each item.",
                "Preserve original links exactly.",
                "Respect config.language and the prompt texts in prompts.",
            ],
        },
        "groups": [
            {
                "group_id": group.get("group_id"),
                "label": group.get("label"),
                "source_types": group.get("source_types", []),
                "limit": group.get("limit", 0),
                "item_count": len(group.get("items", [])),
                "items": [payload_item(item) for item in group.get("items", [])],
            }
            for group in groups
        ],
        "items": [payload_item(item) for item in items],
        "prompts": load_prompt_texts(),
        "errors": feed_payload.get("errors") or [],
    }


def command_configure(args: argparse.Namespace) -> int:
    profile = load_profile()
    profile = update_profile_from_args(profile, args)
    save_profile(profile)
    json.dump(profile, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def command_show_profile(_args: argparse.Namespace) -> int:
    json.dump(load_profile(), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def command_show_state(_args: argparse.Namespace) -> int:
    json.dump(load_state(), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def command_show_service(_args: argparse.Namespace) -> int:
    json.dump(load_service_config(), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def command_configure_service(args: argparse.Namespace) -> int:
    service_config = load_service_config()
    if args.feed_url is not None:
        service_config["feed_url"] = args.feed_url
        service_config["scoutx_feed_url"] = args.feed_url
    if arg_value(args, "scoutx_feed_url") is not None:
        service_config["scoutx_feed_url"] = args.scoutx_feed_url
        service_config["feed_url"] = args.scoutx_feed_url
    if arg_value(args, "x_feed_url") is not None:
        service_config["x_feed_url"] = args.x_feed_url
    if arg_value(args, "podcast_feed_url") is not None:
        service_config["podcast_feed_url"] = args.podcast_feed_url
    if args.meta_url is not None:
        service_config["meta_url"] = args.meta_url
    if args.timeout_seconds is not None:
        service_config["timeout_seconds"] = args.timeout_seconds
    save_service_config(service_config)
    json.dump(service_config, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def command_preview(args: argparse.Namespace) -> int:
    profile = load_profile()
    feed_payload = fetch_selected_feed_payload(profile, args)
    message_group = arg_value(args, "message_group") or "all"
    groups = build_digest_groups(profile, feed_payload, message_group=message_group)
    items = flatten_digest_groups(groups)
    generated_at = str(feed_payload.get("generated_at") or utcnow_iso())

    state = load_state()
    state["last_preview_at"] = utcnow_iso()
    state["last_feed_fetch_at"] = generated_at
    state["last_digest_item_ids"] = [item["content_id"] for item in items if item["content_id"]]
    save_state(state)

    if args.json:
        payload = {
            "generated_at": generated_at,
            "profile": profile,
            "groups": groups,
            "items": items,
        }
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    sys.stdout.write(render_digest_groups(profile, groups, generated_at))
    return 0


def command_deliver(args: argparse.Namespace) -> int:
    preview_args = argparse.Namespace(
        feed_url=args.feed_url,
        feed_file=args.feed_file,
        x_feed_url=arg_value(args, "x_feed_url"),
        x_feed_file=arg_value(args, "x_feed_file"),
        podcast_feed_url=arg_value(args, "podcast_feed_url"),
        podcast_feed_file=arg_value(args, "podcast_feed_file"),
        message_group=arg_value(args, "message_group") or "all",
        json=False,
    )
    return command_preview(preview_args)


def command_prepare_digest(args: argparse.Namespace) -> int:
    profile = load_profile()
    feed_payload = fetch_selected_feed_payload(profile, args)
    message_group = arg_value(args, "message_group") or "all"
    groups = build_digest_groups(profile, feed_payload, message_group=message_group)
    items = flatten_digest_groups(groups)

    state = load_state()
    state["last_preview_at"] = utcnow_iso()
    state["last_feed_fetch_at"] = str(feed_payload.get("generated_at") or utcnow_iso())
    state["last_digest_item_ids"] = [item["content_id"] for item in items if item["content_id"]]
    save_state(state)

    payload = build_prepare_digest_payload(profile, feed_payload, groups)
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def build_openclaw_cron_expression(profile: dict[str, Any]) -> str:
    schedule = profile.get("schedule") or {}
    time_value = str(schedule.get("time") or "09:00").strip() or "09:00"
    if ":" in time_value:
        hour_str, minute_str = time_value.split(":", 1)
    else:
        hour_str, minute_str = time_value, "00"

    hour = int(hour_str)
    minute = int(minute_str)
    frequency = str(schedule.get("frequency") or "daily").strip().lower()
    if frequency == "weekly":
        days = [str(value).strip().lower() for value in schedule.get("days") or []]
        cron_days = [DAY_TO_CRON[day] for day in days if day in DAY_TO_CRON]
        if not cron_days:
            cron_days = [DAY_TO_CRON["mon"]]
        return f"{minute} {hour} * * {','.join(cron_days)}"
    return f"{minute} {hour} * * *"


def build_selected_feed_urls(
    profile: dict[str, Any],
    service_config: dict[str, Any],
    *,
    feed_url: str | None = None,
    x_feed_url: str | None = None,
    podcast_feed_url: str | None = None,
    message_group: str | None = "all",
) -> dict[str, str]:
    explicit_urls = {
        "scoutx": feed_url,
        "x": x_feed_url,
        "podcast": podcast_feed_url,
    }
    feed_urls: dict[str, str] = {}
    for source_type in source_types_for_message_group(profile, message_group):
        env_value = os.getenv(SOURCE_TYPE_ENV_VARS[source_type])
        resolved = explicit_urls[source_type] or env_value or service_feed_url(service_config, source_type)
        feed_urls[source_type] = ensure_real_feed_url(resolved)
    return feed_urls


def feed_env_prefix(feed_urls: dict[str, str]) -> str:
    parts = []
    for source_type, feed_url in feed_urls.items():
        parts.append(f"{SOURCE_TYPE_ENV_VARS[source_type]}={shlex.quote(feed_url)}")
    return " ".join(parts)


def build_openclaw_cron_command(
    profile: dict[str, Any],
    *,
    feed_urls: dict[str, str],
    script_path: str,
    name: str,
    agent: str,
    session: str,
    channel: str | None,
    to: str | None,
    timeout_seconds: int,
    message_group: str = "all",
) -> str:
    cron_expr = build_openclaw_cron_expression(profile)
    resolved_channel, resolved_to = resolve_openclaw_delivery(profile, channel=channel, to=to)
    env_prefix = feed_env_prefix(feed_urls)
    deliver_parts = ["python3", script_path, "deliver"]
    if message_group != "all":
        deliver_parts.extend(["--message-group", message_group])
    deliver_command = " ".join(shlex.quote(part) for part in deliver_parts)
    run_command = f"{env_prefix} {deliver_command}".strip()
    message = (
        f"Run `{run_command}`, "
        "then return the command output verbatim as your final answer. "
        "Do not rewrite, summarize, or reformat it."
    )
    parts = [
        "openclaw",
        "cron",
        "add",
        "--name",
        name,
        "--cron",
        cron_expr,
        "--agent",
        agent,
        "--session",
        session,
        "--message",
        message,
        "--announce",
        "--channel",
        resolved_channel,
    ]
    if resolved_to:
        parts.extend(["--to", resolved_to])
    parts.extend(["--best-effort-deliver", "--exact", "--timeout-seconds", str(timeout_seconds)])
    return " ".join(shlex.quote(part) for part in parts)


def build_openclaw_cron_args(
    profile: dict[str, Any],
    *,
    feed_urls: dict[str, str],
    script_path: str,
    name: str,
    agent: str,
    session: str,
    channel: str | None,
    to: str | None,
    timeout_seconds: int,
    message_group: str = "all",
) -> list[str]:
    cron_expr = build_openclaw_cron_expression(profile)
    resolved_channel, resolved_to = resolve_openclaw_delivery(profile, channel=channel, to=to)
    env_prefix = feed_env_prefix(feed_urls)
    deliver_parts = ["python3", script_path, "deliver"]
    if message_group != "all":
        deliver_parts.extend(["--message-group", message_group])
    deliver_command = " ".join(shlex.quote(part) for part in deliver_parts)
    run_command = f"{env_prefix} {deliver_command}".strip()
    message = (
        f"Run `{run_command}`, "
        "then return the command output verbatim as your final answer. "
        "Do not rewrite, summarize, or reformat it."
    )
    args = [
        "openclaw",
        "cron",
        "add",
        "--name",
        name,
        "--cron",
        cron_expr,
        "--agent",
        agent,
        "--session",
        session,
        "--message",
        message,
        "--announce",
        "--channel",
        resolved_channel,
    ]
    if resolved_to:
        args.extend(["--to", resolved_to])
    args.extend(
        [
            "--best-effort-deliver",
            "--exact",
            "--timeout-seconds",
            str(timeout_seconds),
        ]
    )
    return args


def openclaw_message_groups_for_profile(profile: dict[str, Any]) -> list[str]:
    group_ids = selected_message_group_ids(profile, "all")
    if len(group_ids) <= 1:
        return ["all"]
    return group_ids


def openclaw_job_name(base_name: str, message_group: str, *, split: bool) -> str:
    if not split or message_group == "all":
        return base_name
    suffix = MESSAGE_GROUP_NAME_SUFFIXES[message_group]
    return f"{base_name}-{suffix}"


def build_openclaw_job_specs(
    profile: dict[str, Any],
    service_config: dict[str, Any],
    *,
    feed_url: str | None,
    x_feed_url: str | None,
    podcast_feed_url: str | None,
    script_path: str,
    name: str,
    agent: str,
    session: str,
    channel: str | None,
    to: str | None,
    timeout_seconds: int,
) -> list[dict[str, Any]]:
    message_groups = openclaw_message_groups_for_profile(profile)
    split = len(message_groups) > 1
    jobs: list[dict[str, Any]] = []
    for message_group in message_groups:
        job_name = openclaw_job_name(name, message_group, split=split)
        feed_urls = build_selected_feed_urls(
            profile,
            service_config,
            feed_url=feed_url,
            x_feed_url=x_feed_url,
            podcast_feed_url=podcast_feed_url,
            message_group=message_group,
        )
        command = build_openclaw_cron_command(
            profile,
            feed_urls=feed_urls,
            script_path=script_path,
            name=job_name,
            agent=agent,
            session=session,
            channel=channel,
            to=to,
            timeout_seconds=timeout_seconds,
            message_group=message_group,
        )
        jobs.append(
            {
                "name": job_name,
                "message_group": message_group,
                "label": message_group_label(message_group, profile["preferences"].get("language", "zh-CN"))
                if message_group != "all"
                else None,
                "feed_urls": feed_urls,
                "command": command,
                "args": build_openclaw_cron_args(
                    profile,
                    feed_urls=feed_urls,
                    script_path=script_path,
                    name=job_name,
                    agent=agent,
                    session=session,
                    channel=channel,
                    to=to,
                    timeout_seconds=timeout_seconds,
                    message_group=message_group,
                ),
            }
        )
    return jobs


def resolve_openclaw_delivery(
    profile: dict[str, Any],
    *,
    channel: str | None = None,
    to: str | None = None,
) -> tuple[str, str | None]:
    delivery = profile.get("delivery") or {}
    raw_channel = str(channel or delivery.get("channel") or "last").strip()
    raw_to = str(to if to is not None else delivery.get("target") or "").strip()
    if raw_channel in {"", "in_chat", "stdout", "current", "current_chat"}:
        raw_channel = "last"
    if raw_channel == "feishu" and raw_to.startswith("user:ou_"):
        raw_to = raw_to.removeprefix("user:")
    if raw_channel == "feishu" and raw_to.startswith("group:oc_"):
        raw_to = raw_to.removeprefix("group:")
    if raw_channel != "last" and not raw_to:
        raise SystemExit(
            "OpenClaw delivery target is required for external channels. "
            "Pass --to or save it with configure --delivery-target."
        )
    return raw_channel, raw_to or None


def command_show_openclaw_cron(args: argparse.Namespace) -> int:
    profile = load_profile()
    service_config = load_service_config()
    jobs = build_openclaw_job_specs(
        profile,
        service_config,
        feed_url=args.feed_url,
        x_feed_url=arg_value(args, "x_feed_url"),
        podcast_feed_url=arg_value(args, "podcast_feed_url"),
        script_path=args.script_path,
        name=args.name,
        agent=args.agent,
        session=args.session,
        channel=args.channel,
        to=args.to,
        timeout_seconds=args.timeout_seconds,
    )
    if args.json:
        channel, to = resolve_openclaw_delivery(profile, channel=args.channel, to=args.to)
        payload = {
            "name": args.name,
            "cron": build_openclaw_cron_expression(profile),
            "agent": args.agent,
            "session": args.session,
            "channel": channel,
            "to": to,
            "mode": "split" if len(jobs) > 1 else "single",
            "script_path": args.script_path,
            "timeout_seconds": args.timeout_seconds,
            "jobs": [
                {
                    "name": job["name"],
                    "message_group": job["message_group"],
                    "label": job["label"],
                    "feed_urls": job["feed_urls"],
                    "command": job["command"],
                }
                for job in jobs
            ],
        }
        if len(jobs) == 1:
            payload["feed_urls"] = jobs[0]["feed_urls"]
            payload["command"] = jobs[0]["command"]
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    for job in jobs:
        sys.stdout.write(job["command"] + "\n")
    return 0


def command_install_openclaw_cron(args: argparse.Namespace) -> int:
    profile = load_profile()
    service_config = load_service_config()
    jobs = build_openclaw_job_specs(
        profile,
        service_config,
        feed_url=args.feed_url,
        x_feed_url=arg_value(args, "x_feed_url"),
        podcast_feed_url=arg_value(args, "podcast_feed_url"),
        script_path=args.script_path,
        name=args.name,
        agent=args.agent,
        session=args.session,
        channel=args.channel,
        to=args.to,
        timeout_seconds=args.timeout_seconds,
    )

    if not args.apply:
        payload = {
            "mode": "dry_run",
            "delivery_mode": "split" if len(jobs) > 1 else "single",
            "commands": [job["command"] for job in jobs],
            "jobs": [
                {
                    "name": job["name"],
                    "message_group": job["message_group"],
                    "label": job["label"],
                    "feed_urls": job["feed_urls"],
                    "command": job["command"],
                }
                for job in jobs
            ],
        }
        if len(jobs) == 1:
            payload["command"] = jobs[0]["command"]
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    results = []
    for job in jobs:
        completed = subprocess.run(
            job["args"],
            check=False,
            capture_output=True,
            text=True,
        )
        results.append(
            {
                "name": job["name"],
                "message_group": job["message_group"],
                "command": job["command"],
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
    payload = {
        "mode": "apply",
        "delivery_mode": "split" if len(jobs) > 1 else "single",
        "results": results,
    }
    if len(results) == 1:
        payload["command"] = results[0]["command"]
        payload["returncode"] = results[0]["returncode"]
        payload["stdout"] = results[0]["stdout"]
        payload["stderr"] = results[0]["stderr"]
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if all(result["returncode"] == 0 for result in results) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local profile manager and preview client for Follow ScoutX.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    configure_parser = subparsers.add_parser("configure", help="Create or update the local profile")
    configure_parser.add_argument("--frequency", choices=["daily", "weekly"])
    configure_parser.add_argument("--time")
    configure_parser.add_argument("--days")
    configure_parser.add_argument("--language", choices=["zh-CN", "en", "bilingual"])
    configure_parser.add_argument(
        "--source-mode",
        choices=["scoutx", "first_party", "mixed"],
        help="High-level source selection: scoutx, first_party (X + podcast), or mixed",
    )
    configure_parser.add_argument(
        "--source-types",
        help="Comma-separated source types: scoutx,x,podcast",
    )
    configure_parser.add_argument("--delivery-channel")
    configure_parser.add_argument("--delivery-target")
    configure_parser.add_argument("--topics")
    configure_parser.add_argument("--keywords-include")
    configure_parser.add_argument("--keywords-exclude")
    configure_parser.add_argument("--preferred-sources")
    configure_parser.add_argument("--max-items", type=int)
    configure_parser.add_argument(
        "--max-first-party-items",
        type=int,
        help="Maximum items for the first-party message group (X + podcast)",
    )
    configure_parser.add_argument(
        "--max-scoutx-items",
        type=int,
        help="Maximum items for the ScoutX curated media message group",
    )
    configure_parser.add_argument("--length", choices=["short", "medium", "long"])
    configure_parser.add_argument("--tone")
    configure_parser.set_defaults(handler=command_configure)

    show_profile_parser = subparsers.add_parser("show-profile", help="Show the saved local profile")
    show_profile_parser.set_defaults(handler=command_show_profile)

    show_state_parser = subparsers.add_parser("show-state", help="Show the local state file")
    show_state_parser.set_defaults(handler=command_show_state)

    show_service_parser = subparsers.add_parser("show-service", help="Show the bundled central service config")
    show_service_parser.set_defaults(handler=command_show_service)

    configure_service_parser = subparsers.add_parser(
        "configure-service",
        help="Create or update the local service endpoint override used by this installation",
    )
    configure_service_parser.add_argument("--feed-url")
    configure_service_parser.add_argument("--scoutx-feed-url")
    configure_service_parser.add_argument("--x-feed-url")
    configure_service_parser.add_argument("--podcast-feed-url")
    configure_service_parser.add_argument("--meta-url")
    configure_service_parser.add_argument("--timeout-seconds", type=int)
    configure_service_parser.set_defaults(handler=command_configure_service)

    preview_parser = subparsers.add_parser("preview", help="Preview a digest using the saved local profile")
    preview_parser.add_argument("--feed-url")
    preview_parser.add_argument("--feed-file")
    preview_parser.add_argument("--x-feed-url")
    preview_parser.add_argument("--x-feed-file")
    preview_parser.add_argument("--podcast-feed-url")
    preview_parser.add_argument("--podcast-feed-file")
    preview_parser.add_argument("--message-group", choices=MESSAGE_GROUP_CHOICES, default="all")
    preview_parser.add_argument("--json", action="store_true")
    preview_parser.set_defaults(handler=command_preview)

    deliver_parser = subparsers.add_parser(
        "deliver",
        help="Render a final markdown digest suitable for OpenClaw --announce delivery",
    )
    deliver_parser.add_argument("--feed-url")
    deliver_parser.add_argument("--feed-file")
    deliver_parser.add_argument("--x-feed-url")
    deliver_parser.add_argument("--x-feed-file")
    deliver_parser.add_argument("--podcast-feed-url")
    deliver_parser.add_argument("--podcast-feed-file")
    deliver_parser.add_argument("--message-group", choices=MESSAGE_GROUP_CHOICES, default="all")
    deliver_parser.set_defaults(handler=command_deliver)

    prepare_digest_parser = subparsers.add_parser(
        "prepare-digest",
        help="Output a structured JSON payload for prompt-controlled LLM digest generation",
    )
    prepare_digest_parser.add_argument("--feed-url")
    prepare_digest_parser.add_argument("--feed-file")
    prepare_digest_parser.add_argument("--x-feed-url")
    prepare_digest_parser.add_argument("--x-feed-file")
    prepare_digest_parser.add_argument("--podcast-feed-url")
    prepare_digest_parser.add_argument("--podcast-feed-file")
    prepare_digest_parser.add_argument("--message-group", choices=MESSAGE_GROUP_CHOICES, default="all")
    prepare_digest_parser.set_defaults(handler=command_prepare_digest)

    openclaw_cron_parser = subparsers.add_parser(
        "show-openclaw-cron",
        help="Print a recommended openclaw cron add command using the saved schedule and service config",
    )
    openclaw_cron_parser.add_argument("--feed-url")
    openclaw_cron_parser.add_argument(
        "--script-path",
        default=current_script_path(),
    )
    openclaw_cron_parser.add_argument("--x-feed-url")
    openclaw_cron_parser.add_argument("--podcast-feed-url")
    openclaw_cron_parser.add_argument("--name", default="follow-scoutx-daily")
    openclaw_cron_parser.add_argument("--agent", default="main")
    openclaw_cron_parser.add_argument("--session", default="isolated")
    openclaw_cron_parser.add_argument("--channel")
    openclaw_cron_parser.add_argument("--to")
    openclaw_cron_parser.add_argument("--timeout-seconds", type=int, default=120)
    openclaw_cron_parser.add_argument("--json", action="store_true")
    openclaw_cron_parser.set_defaults(handler=command_show_openclaw_cron)

    install_openclaw_cron_parser = subparsers.add_parser(
        "install-openclaw-cron",
        help="Create the recommended OpenClaw cron job for this Follow ScoutX installation",
    )
    install_openclaw_cron_parser.add_argument("--feed-url")
    install_openclaw_cron_parser.add_argument(
        "--script-path",
        default=current_script_path(),
    )
    install_openclaw_cron_parser.add_argument("--x-feed-url")
    install_openclaw_cron_parser.add_argument("--podcast-feed-url")
    install_openclaw_cron_parser.add_argument("--name", default="follow-scoutx-daily")
    install_openclaw_cron_parser.add_argument("--agent", default="main")
    install_openclaw_cron_parser.add_argument("--session", default="isolated")
    install_openclaw_cron_parser.add_argument("--channel")
    install_openclaw_cron_parser.add_argument("--to")
    install_openclaw_cron_parser.add_argument("--timeout-seconds", type=int, default=120)
    install_openclaw_cron_parser.add_argument("--apply", action="store_true")
    install_openclaw_cron_parser.set_defaults(handler=command_install_openclaw_cron)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
