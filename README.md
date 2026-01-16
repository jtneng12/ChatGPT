# Shanghainese IPA-to-Audio Dictionary Builder

This project collects IPA for Shanghainese characters from the WuGniu dictionary and then drives [ipa-reader.com](https://ipa-reader.com/) to generate audio for full sentences. It is designed to be a **local, scriptable workflow** so you can build a reusable audio corpus.

> ⚠️ **Important**: Make sure your use of WuGniu and IPA Reader complies with their terms of service. You may need to add delays or request permission if you are doing large-scale downloads.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install
```

### 1) Add sentences

Put sentences (one per line) in `data/sentences.txt`. A small example is provided in `data/sample_sentences.txt`.

### 2) Fetch IPA for characters

```bash
python -m shanghainese_audio_dictionary.fetch_ipa \
  --input data/sentences.txt \
  --cache data/ipa_cache.json \
  --output data/sentences_with_ipa.json
```

This does the following:

* Splits each sentence into characters.
* Queries WuGniu for the IPA of each character.
* Saves a cache so you do not re-query the same character.
* Emits a JSON file containing sentences with their IPA string.

If WuGniu changes its HTML structure, open `shanghainese_audio_dictionary/fetch_ipa.py` and adjust the selectors in `WUGNIU_SELECTORS`.

### 3) Generate audio via IPA Reader

```bash
python -m shanghainese_audio_dictionary.ipa_reader \
  --input data/sentences_with_ipa.json \
  --output-dir outputs
```

The script uses Playwright to open ipa-reader.com, paste the IPA for each sentence, and download audio files.

### 4) Concatenate audio (optional)

If you want a single audio file, use `ffmpeg` to concatenate the clips:

```bash
ffmpeg -f concat -safe 0 -i outputs/concat_list.txt -c copy outputs/full_audio.mp3
```

The `ipa_reader` script can optionally emit `concat_list.txt` for you (`--concat-list`).

## Troubleshooting

* **403/blocked from WuGniu**: try `--user-agent` or `--min-delay` to slow requests, or fetch IPA manually and use the `--manual-ipa` option.
* **Download fails on IPA Reader**: run with `--headed` to watch the browser and adjust selectors in `ipa_reader.py`.

## Folder structure

```
shanghainese_audio_dictionary/
  fetch_ipa.py       # Scrapes IPA and builds sentence IPA strings
  ipa_reader.py      # Uses Playwright to download audio from IPA Reader
  pipeline.py        # Convenience wrapper to run end-to-end
  utils.py           # Shared helpers

data/
  sample_sentences.txt
  ipa_cache.json     # generated
  sentences_with_ipa.json # generated

outputs/
  sentence_0001.mp3  # generated audio
```

## End-to-end (single command)

```bash
python -m shanghainese_audio_dictionary.pipeline \
  --sentences data/sentences.txt \
  --cache data/ipa_cache.json \
  --output-dir outputs \
  --concat-list
```

## VS Code setup

This repo ships with VS Code launch configs and tasks for the common flows:

* **Launch**: `Fetch IPA (sentences.txt)`, `Generate Audio (IPA Reader)`, `Run Pipeline (end-to-end)`
* **Tasks**: `Install deps`, `Fetch IPA`, `Generate Audio`, `Run Pipeline`

Open the Run and Debug panel to pick a launch config, or run tasks from the Command Palette.
