from __future__ import annotations

import argparse
from pathlib import Path

from shanghainese_audio_dictionary.fetch_ipa import (
    FetchConfig,
    build_sentence_ipa,
    load_manual_ipa,
    run_fetch,
)
from shanghainese_audio_dictionary.ipa_reader import download_audio
from shanghainese_audio_dictionary.utils import expand_user, save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="End-to-end Shanghainese IPA audio pipeline")
    parser.add_argument("--sentences", required=True, help="Text file with one sentence per line")
    parser.add_argument("--cache", required=True, help="JSON cache for character IPA")
    parser.add_argument("--output-dir", required=True, help="Directory for audio output")
    parser.add_argument("--manual-ipa", help="Optional JSON with manual IPA overrides")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=60000)
    parser.add_argument("--min-delay", type=float, default=1.0)
    parser.add_argument("--user-agent", default="Mozilla/5.0 (compatible; ShanghaineseDictionaryBot/1.0)")
    parser.add_argument("--concat-list", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sentences_path = expand_user(args.sentences)
    cache_path = expand_user(args.cache)
    output_dir = expand_user(args.output_dir)
    manual_path = expand_user(args.manual_ipa) if args.manual_ipa else None

    sentences = [line.strip() for line in sentences_path.read_text(encoding="utf-8").splitlines()]
    sentences = [line for line in sentences if line]

    config = FetchConfig(cache_path=cache_path, user_agent=args.user_agent, min_delay=args.min_delay)
    manual_ipa = load_manual_ipa(manual_path)
    cache = run_fetch(sentences, config, manual_ipa=manual_ipa)

    payload = [{"sentence": sentence, "ipa": build_sentence_ipa(sentence, cache)} for sentence in sentences]

    sentences_ipa_path = output_dir / "sentences_with_ipa.json"
    save_json(sentences_ipa_path, payload)

    concat_path = output_dir / "concat_list.txt" if args.concat_list else None
    download_audio(payload, output_dir, args.headed, args.timeout_ms, concat_path)


if __name__ == "__main__":
    main()
