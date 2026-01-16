from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from playwright.sync_api import sync_playwright
from tqdm import tqdm

from shanghainese_audio_dictionary.utils import (
    expand_user,
    load_json,
    normalize_whitespace,
    save_json,
    write_concat_list,
)

IPA_READER_URL = "https://ipa-reader.com/"

INPUT_SELECTORS = [
    "textarea#ipa-text",
    "textarea#ipaText",
    "textarea[name='ipa']",
    "textarea",
]

PLAY_BUTTON_SELECTORS = [
    "button#play",
    "button:has-text('Read')",
    "button:has-text('Play')",
]

DOWNLOAD_SELECTORS = [
    "a:has-text('Download MP3')",
    "a:has-text('Download WAV')",
    "button:has-text('Download')",
]


def find_first(page, selectors: List[str]):
    for selector in selectors:
        locator = page.locator(selector)
        if locator.count() > 0:
            return locator.first
    return None


def load_sentences(path: Path) -> List[Dict[str, str]]:
    data = load_json(path, [])
    if not isinstance(data, list):
        raise ValueError("Input must be a list of objects with 'sentence' and 'ipa' keys.")
    return data


def download_audio(
    items: Iterable[Dict[str, str]],
    output_dir: Path,
    headed: bool,
    timeout_ms: int,
    concat_list: Optional[Path],
) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: List[Path] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed)
        page = browser.new_page()
        page.goto(IPA_READER_URL, timeout=timeout_ms)

        input_box = find_first(page, INPUT_SELECTORS)
        if input_box is None:
            raise RuntimeError("Could not locate IPA input box on ipa-reader.com")

        for index, item in enumerate(tqdm(list(items), desc="Generating audio"), start=1):
            ipa_text = normalize_whitespace(item.get("ipa", ""))
            if not ipa_text:
                continue

            filename = f"sentence_{index:04d}.mp3"
            target_path = output_dir / filename

            input_box.fill(ipa_text)
            play_button = find_first(page, PLAY_BUTTON_SELECTORS)
            if play_button:
                play_button.click()

            download_button = find_first(page, DOWNLOAD_SELECTORS)
            if download_button is None:
                raise RuntimeError("Could not find a download button on ipa-reader.com")

            with page.expect_download(timeout=timeout_ms) as download_info:
                download_button.click()
            download = download_info.value
            download.save_as(target_path)
            saved_paths.append(target_path)

        browser.close()

    if concat_list:
        write_concat_list(saved_paths, concat_list)

    return saved_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate audio via IPA Reader")
    parser.add_argument("--input", required=True, help="JSON with sentence IPA")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=60000)
    parser.add_argument("--concat-list", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = expand_user(args.input)
    output_dir = expand_user(args.output_dir)
    concat_path = output_dir / "concat_list.txt" if args.concat_list else None

    items = load_sentences(input_path)
    download_audio(items, output_dir, args.headed, args.timeout_ms, concat_path)


if __name__ == "__main__":
    main()
