from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from shanghainese_audio_dictionary.utils import (
    expand_user,
    load_json,
    normalize_whitespace,
    save_json,
    split_sentence,
)

IPA_PATTERN = re.compile(r"[˥˦˧˨˩a-zA-Zɕʑŋɔɤøɿʮʐɥʔʦʨ˩˧˦˥˨˩]+")

WUGNIU_ENTRY_URL = "https://www.wugniu.com/entry/{char}"
WUGNIU_SEARCH_URL = "https://www.wugniu.com/s/{char}"

WUGNIU_SELECTORS = [
    "span.ipa",
    "span.yinbiao",
    "span.pronunciation",
    "div.ipa",
    "div.yinbiao",
]


@dataclass
class FetchConfig:
    cache_path: Path
    user_agent: str
    min_delay: float


class WugniuClient:
    def __init__(self, config: FetchConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})

    def fetch_ipa(self, char: str) -> Optional[str]:
        for url in (WUGNIU_ENTRY_URL, WUGNIU_SEARCH_URL):
            resolved_url = url.format(char=char)
            response = self.session.get(resolved_url, timeout=15)
            if response.status_code != 200:
                continue
            ipa = self._parse_ipa(response.text)
            if ipa:
                return ipa
        return None

    @staticmethod
    def _parse_ipa(html: str) -> Optional[str]:
        soup = BeautifulSoup(html, "html.parser")
        for selector in WUGNIU_SELECTORS:
            node = soup.select_one(selector)
            if node and node.get_text(strip=True):
                return normalize_whitespace(node.get_text(strip=True))
        text = soup.get_text(" ")
        matches = IPA_PATTERN.findall(text)
        if matches:
            return normalize_whitespace(matches[0])
        return None


def build_sentence_ipa(sentence: str, char_to_ipa: Dict[str, str]) -> str:
    chars = split_sentence(sentence)
    ipa_tokens = [char_to_ipa.get(char, "") for char in chars]
    return normalize_whitespace(" ".join(token for token in ipa_tokens if token))


def run_fetch(
    sentences: Iterable[str],
    config: FetchConfig,
    manual_ipa: Dict[str, str] | None = None,
) -> Dict[str, str]:
    cache: Dict[str, str] = load_json(config.cache_path, {})
    if manual_ipa:
        cache.update({key: value for key, value in manual_ipa.items() if value})

    client = WugniuClient(config)
    for sentence in tqdm(list(sentences), desc="Fetching IPA"):
        for char in split_sentence(sentence):
            if char in cache:
                continue
            ipa = client.fetch_ipa(char)
            if ipa:
                cache[char] = ipa
            time.sleep(config.min_delay)
    save_json(config.cache_path, cache)
    return cache


def load_manual_ipa(path: Optional[Path]) -> Dict[str, str]:
    if not path:
        return {}
    raw = load_json(path, {})
    return {str(key): str(value) for key, value in raw.items()}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Shanghainese IPA from WuGniu")
    parser.add_argument("--input", required=True, help="Text file with one sentence per line")
    parser.add_argument("--cache", required=True, help="JSON cache for character IPA")
    parser.add_argument("--output", required=True, help="Output JSON with sentence IPA")
    parser.add_argument(
        "--manual-ipa",
        help="Optional JSON file with manual IPA overrides: {" "char": "ipa"}",
    )
    parser.add_argument(
        "--user-agent",
        default="Mozilla/5.0 (compatible; ShanghaineseDictionaryBot/1.0)",
    )
    parser.add_argument("--min-delay", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = expand_user(args.input)
    cache_path = expand_user(args.cache)
    output_path = expand_user(args.output)
    manual_path = expand_user(args.manual_ipa) if args.manual_ipa else None

    sentences = [line.strip() for line in input_path.read_text(encoding="utf-8").splitlines()]
    sentences = [line for line in sentences if line]

    config = FetchConfig(cache_path=cache_path, user_agent=args.user_agent, min_delay=args.min_delay)
    manual_ipa = load_manual_ipa(manual_path)
    cache = run_fetch(sentences, config, manual_ipa=manual_ipa)

    payload: List[Dict[str, str]] = []
    for sentence in sentences:
        payload.append(
            {
                "sentence": sentence,
                "ipa": build_sentence_ipa(sentence, cache),
            }
        )

    save_json(output_path, payload)


if __name__ == "__main__":
    main()
