"""Export labeled drawing attempts from Supabase to local filesystem.

Downloads completed attempts where is_correct=True (verified by user) and
organizes them into data/raw/{letter}/ directories for training.

Usage:
    python collect.py --output ../../data/raw

Requires SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.
"""

import argparse
import os

import requests
from supabase import create_client


def main():
    parser = argparse.ArgumentParser(description="Collect training data from Supabase")
    parser.add_argument("--output", default="../../data/raw")
    args = parser.parse_args()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables")
        return

    client = create_client(url, key)

    result = (
        client.table("checker_attempt")
        .select("id, image_url, checker_symbol!inner(letter)")
        .eq("status", "completed")
        .eq("is_correct", True)
        .execute()
    )

    if not result.data:
        print("No verified attempts found")
        return

    os.makedirs(args.output, exist_ok=True)
    downloaded = 0

    for row in result.data:
        letter = row["checker_symbol"]["letter"]
        letter_dir = os.path.join(args.output, letter)
        os.makedirs(letter_dir, exist_ok=True)

        image_url = row["image_url"]
        filename = f"{row['id']}.png"
        filepath = os.path.join(letter_dir, filename)

        if os.path.exists(filepath):
            continue

        try:
            resp = requests.get(image_url, timeout=10)
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(resp.content)
            downloaded += 1
        except Exception as e:
            print(f"  Failed to download {image_url}: {e}")

    print(f"Downloaded {downloaded} images to {args.output}")


if __name__ == "__main__":
    main()
