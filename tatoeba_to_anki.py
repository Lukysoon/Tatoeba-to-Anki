#!/usr/bin/env python3
import argparse
import csv
import os
import sqlite3
import subprocess
import requests
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

class TatoebaToAnki:
    def __init__(self, learning_lang, base_lang, output_dir="output"):
        """
        Initialize converter
        learning_lang: language you want to learn (e.g., 'jpn' for Japanese)
        base_lang: your native/known language (e.g., 'eng' for English)
        """
        self.learning_lang = learning_lang
        self.base_lang = base_lang
        self.output_dir = output_dir
        self.db_path = "tatoeba.sqlite3"
        self.csv_dir = "csv"
        self.audio_dir = os.path.join(output_dir, "audio")
        
        # Create necessary directories
        os.makedirs(self.csv_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)

    def download_csv_files(self):
        """Download and prepare CSV files from Tatoeba"""
        print("Downloading CSV files...")
        files = [
            "sentences.tar.bz2",
            "links.tar.bz2",
            "tags.tar.bz2",
            "sentences_with_audio.tar.bz2"
        ]
        
        for file in files:
            url = f"https://downloads.tatoeba.org/exports/{file}"
            output_path = os.path.join(self.csv_dir, file)
            
            if not os.path.exists(output_path):
                print(f"Downloading {file}...")
                response = requests.get(url, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                
                with open(output_path, 'wb') as f, tqdm(
                    total=total_size,
                    unit='iB',
                    unit_scale=True
                ) as pbar:
                    for data in response.iter_content(chunk_size=1024):
                        size = f.write(data)
                        pbar.update(size)
            
            # Extract
            print(f"Extracting {file}...")
            subprocess.run(['tar', 'jxf', output_path, '-C', self.csv_dir])

        # Prepare files
        print("Preparing CSV files...")
        with open(os.path.join(self.csv_dir, 'sentences.csv'), 'r', encoding='utf-8') as f:
            content = f.read()
        with open(os.path.join(self.csv_dir, 'sentences.escaped_quotes.csv'), 'w', encoding='utf-8') as f:
            f.write(content.replace('"', '""'))

        with open(os.path.join(self.csv_dir, 'tags.csv'), 'r', encoding='utf-8') as f:
            content = f.read()
        with open(os.path.join(self.csv_dir, 'tags.escaped_quotes.csv'), 'w', encoding='utf-8') as f:
            f.write(content.replace('"', '""'))

    def create_database(self):
        """Create and populate SQLite database"""
        print("Creating database...")
        
        # Remove existing database if it exists
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Create tables
        c.executescript('''
            PRAGMA foreign_keys = OFF;

            CREATE TABLE IF NOT EXISTS sentences (
                sentence_id INTEGER PRIMARY KEY,
                lang TEXT,
                text TEXT
            );
            
            CREATE TABLE IF NOT EXISTS sentences_with_audio (
                sentence_id INTEGER PRIMARY KEY,
                username TEXT,
                license TEXT,
                attribution_url TEXT
            );
            
            CREATE TABLE IF NOT EXISTS links (
                sentence_id INTEGER,
                translation_id INTEGER
            );
            
            CREATE TABLE IF NOT EXISTS tags (
                sentence_id INTEGER,
                tag_name TEXT
            );

            CREATE INDEX IF NOT EXISTS links_index ON links(sentence_id, translation_id);
            CREATE INDEX IF NOT EXISTS tags_index ON tags(sentence_id, tag_name);
        ''')

        # Import data
        print("Importing data into database...")
        
        def import_sentences():
            print("Importing sentences...")
            with open(os.path.join(self.csv_dir, 'sentences.escaped_quotes.csv'), 'r', encoding='utf-8') as f:
                next(f)  # Skip header
                batch = []
                for line in f:
                    try:
                        id_, lang, text = line.strip().split('\t')
                        batch.append((int(id_), lang, text.strip('"')))
                        if len(batch) >= 1000:
                            c.executemany("INSERT OR IGNORE INTO sentences VALUES (?, ?, ?)", batch)
                            conn.commit()
                            batch = []
                    except Exception as e:
                        print(f"Error processing sentence: {e}")
                        continue
                if batch:
                    c.executemany("INSERT OR IGNORE INTO sentences VALUES (?, ?, ?)", batch)
                    conn.commit()

        def import_sentences_with_audio():
            print("Importing sentences with audio...")
            with open(os.path.join(self.csv_dir, 'sentences_with_audio.csv'), 'r', encoding='utf-8') as f:
                next(f)  # Skip header
                batch = []
                for line in f:
                    try:
                        parts = line.strip().split('\t')
                        if len(parts) >= 4:  # Ensure we have all required fields
                            batch.append((int(parts[0]), parts[1], parts[2], parts[3]))
                            if len(batch) >= 1000:
                                c.executemany("INSERT OR IGNORE INTO sentences_with_audio VALUES (?, ?, ?, ?)", batch)
                                conn.commit()
                                batch = []
                    except Exception as e:
                        print(f"Error processing audio sentence: {e}")
                        continue
                if batch:
                    c.executemany("INSERT OR IGNORE INTO sentences_with_audio VALUES (?, ?, ?, ?)", batch)
                    conn.commit()

        def import_links():
            print("Importing links...")
            with open(os.path.join(self.csv_dir, 'links.csv'), 'r', encoding='utf-8') as f:
                next(f)  # Skip header
                batch = []
                for line in f:
                    try:
                        id1, id2 = line.strip().split('\t')
                        batch.append((int(id1), int(id2)))
                        if len(batch) >= 1000:
                            c.executemany("INSERT OR IGNORE INTO links VALUES (?, ?)", batch)
                            conn.commit()
                            batch = []
                    except Exception as e:
                        print(f"Error processing link: {e}")
                        continue
                if batch:
                    c.executemany("INSERT OR IGNORE INTO links VALUES (?, ?)", batch)
                    conn.commit()

        def import_tags():
            print("Importing tags...")
            with open(os.path.join(self.csv_dir, 'tags.escaped_quotes.csv'), 'r', encoding='utf-8') as f:
                next(f)  # Skip header
                batch = []
                for line in f:
                    try:
                        id_, tag = line.strip().split('\t')
                        batch.append((int(id_), tag.strip('"')))
                        if len(batch) >= 1000:
                            c.executemany("INSERT OR IGNORE INTO tags VALUES (?, ?)", batch)
                            conn.commit()
                            batch = []
                    except Exception as e:
                        print(f"Error processing tag: {e}")
                        continue
                if batch:
                    c.executemany("INSERT OR IGNORE INTO tags VALUES (?, ?)", batch)
                    conn.commit()

        try:
            import_sentences()
            import_sentences_with_audio()
            import_links()
            import_tags()
        except Exception as e:
            print(f"Error during database creation: {e}")
            raise

        conn.close()

    def generate_anki_csv(self):
        """Generate Anki-importable CSV file"""
        print("Generating Anki CSV file...")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Modified query to get sentences in both languages
        query = f"""
        WITH learning_sentences AS (
            SELECT 
                s1.sentence_id,
                s1.text as learning_text,
                s2.text as base_text,
                s1.sentence_id as audio_id
            FROM sentences s1
            JOIN links ON s1.sentence_id = links.sentence_id
            JOIN sentences s2 ON links.translation_id = s2.sentence_id
            WHERE 
                s1.lang = '{self.learning_lang}'
                AND s2.lang = '{self.base_lang}'
                AND s1.sentence_id IN (SELECT sentence_id FROM sentences_with_audio)
        )
        SELECT
            sentence_id,
            learning_text,
            base_text,
            "[sound:tatoeba_" || "{self.learning_lang}" || "_" || audio_id || ".mp3]",
            "<ul class=""tags""><li>" ||
            COALESCE(
                (
                    SELECT group_concat(tag_name, "</li><li>")
                    FROM tags
                    WHERE tags.sentence_id = learning_sentences.sentence_id
                ), ''
            )
            || "</li></ul>"
        FROM learning_sentences
        """

        output_file = os.path.join(self.output_dir, f'{self.learning_lang}_from_{self.base_lang}.csv')
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter='\t',
                              quotechar='|', quoting=csv.QUOTE_MINIMAL)
            # Write header
            writer.writerow(['sentence_id', 'learning_text', 'base_text', 'audio', 'tags'])
            # Write data
            for row in c.execute(query):
                writer.writerow(row)

        conn.close()

    def download_audio(self):
        """Download audio files for sentences"""
        print("Downloading audio files...")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        query = f"""
        SELECT sentence_id
        FROM sentences
        WHERE
            lang = '{self.learning_lang}' AND
            sentence_id IN (SELECT sentence_id FROM sentences_with_audio)
        """

        def download_file(sentence_id):
            url = f"https://audio.tatoeba.org/sentences/{self.learning_lang}/{sentence_id}.mp3"
            output_path = os.path.join(self.audio_dir, f"tatoeba_{self.learning_lang}_{sentence_id}.mp3")
            
            if not os.path.exists(output_path):
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        with open(output_path, 'wb') as f:
                            f.write(response.content)
                except Exception as e:
                    print(f"Failed to download audio for sentence {sentence_id}: {e}")

        sentence_ids = [row[0] for row in c.execute(query)]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(tqdm(executor.map(download_file, sentence_ids), 
                     total=len(sentence_ids), 
                     desc="Downloading audio files"))

        conn.close()

    def run(self):
        """Run the complete process"""
        print(f"Starting Tatoeba to Anki conversion for {self.learning_lang} (from {self.base_lang})...")
        try:
            self.download_csv_files()
            self.create_database()
            self.generate_anki_csv()
            self.download_audio()
            print("\nProcess completed!")
            print(f"\nOutput files are in the '{self.output_dir}' directory:")
            print(f"1. CSV file: {self.learning_lang}_from_{self.base_lang}.csv")
            print(f"2. Audio files: {self.audio_dir}/")
            print("\nNext steps:")
            print("1. Import the CSV file into Anki (File → Import)")
            print("2. Copy the MP3 files to your Anki media collection directory")
            print("3. Download Tatoeba's logo and save it as '_tatoeba.svg' in your media collection")
        except Exception as e:
            print(f"An error occurred: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(
        description="Convert Tatoeba sentences to Anki deck with audio")
    parser.add_argument("-t", "--target", type=str,
                       help="target language you want to learn (e.g., 'jpn' for Japanese)",
                       required=True)
    parser.add_argument("-b", "--base", type=str,
                       help="your base/native language (e.g., 'eng' for English)",
                       required=True)
    parser.add_argument("-o", "--output", type=str,
                       help="output directory",
                       default="output")
    
    args = parser.parse_args()
    
    converter = TatoebaToAnki(args.target, args.base, args.output)
    converter.run()

if __name__ == "__main__":
    main()
