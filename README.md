# Tatoeba to Anki Converter

This script creates Anki flashcard decks for language learning using sentences and audio from the Tatoeba Project. It generates bilingual cards with native audio recordings.

## Features

- Creates cards with both target language and base language text
- Includes native speaker audio recordings
- Adds relevant tags from Tatoeba
- Automatically downloads and organizes all necessary files
- Supports any language pair available on Tatoeba

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)
- Anki desktop application

## Installation

1. Clone or download this repository:
```bash
git clone [repository-url]
cd [repository-directory]
```

2. Create and activate a virtual environment:

On Windows:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

On macOS/Linux:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

3. Install the required Python packages:
```bash
pip install -r requirements.txt
```

4. When you're done using the script, you can deactivate the virtual environment:
```bash
deactivate
```

## Usage

Make sure your virtual environment is activated, then run:

```bash
python tatoeba_to_anki.py -t TARGET_LANG -b BASE_LANG
```

Where:
- `TARGET_LANG` is the language you want to learn (e.g., 'jpn' for Japanese)
- `BASE_LANG` is your native/known language (e.g., 'eng' for English)

Examples:
```bash
# Learning Finnish from English
python tatoeba_to_anki.py -t fin -b eng

# Learning Japanese from English
python tatoeba_to_anki.py -t jpn -b eng

# Learning German from Spanish
python tatoeba_to_anki.py -t deu -b spa
```

## Output

The script creates an 'output' directory containing:
1. A CSV file named `[target_lang]_from_[base_lang].csv` with:
   - Sentence text in both languages
   - Audio references
   - Tatoeba tags
2. An 'audio' subdirectory with MP3 files for all sentences

## Importing to Anki


1. Import the generated CSV file:
   - Go to File → Import
   - Select the generated CSV file
   - Make sure fields match correctly
   - Check "Allow HTML in fields"

2. Copy the audio files:
   - Locate your Anki media collection directory
   - Copy all MP3 files from the output/audio directory to your Anki media collection
   - Download Tatoeba's logo and save it as '_tatoeba.svg' in your media collection

## Language Codes

Use ISO 639-3 codes for languages. Common examples:
- ces: Czech
- tur: Turkish
- eng: English
- jpn: Japanese
- deu: German
- fra: French
- spa: Spanish
- rus: Russian
- kor: Korean
- fin: Finnish

For a complete list of language codes, visit [ISO 639-3 codes](https://iso639-3.sil.org/code_tables/639/data).

## Note

- Make sure you have enough disk space as the script will download:
  - Tatoeba CSV data files (several GB)
  - Audio files for all sentences in the target language
- The script creates cards only for sentences that have audio recordings
- The quality of the deck depends on available translations between your chosen language pair
- Always activate the virtual environment before running the script
- If you need to rerun the script later, just activate the virtual environment again - no need to reinstall dependencies

## Troubleshooting

If you get any dependency-related errors:
1. Make sure your virtual environment is activated (you should see `(venv)` in your terminal)
2. Try updating pip: `pip install --upgrade pip`
3. Reinstall dependencies: `pip install -r requirements.txt`
