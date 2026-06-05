"""Export labeled drawing attempts from the database to local filesystem.

Queries completed attempts where is_correct=True (verified by user) and
organizes them into data/raw/{letter}/ directories for training.

Usage:
    python manage.py shell -c "from ml.train.collect import main; main()"

    Or from the project root:
    docker compose exec backend python manage.py shell -c "from ml.train.collect import main; main('../../data/raw')"
"""

import os
import shutil

from checker.models import Attempt


def main(output_dir="../../data/raw"):
    attempts = (
        Attempt.objects.filter(status="completed", is_correct=True)
        .select_related("symbol")
    )

    if not attempts.exists():
        print("No verified attempts found")
        return

    os.makedirs(output_dir, exist_ok=True)
    exported = 0

    for attempt in attempts:
        letter = attempt.symbol.letter
        letter_dir = os.path.join(output_dir, letter)
        os.makedirs(letter_dir, exist_ok=True)

        filename = f"{attempt.id}.png"
        filepath = os.path.join(letter_dir, filename)

        if os.path.exists(filepath):
            continue

        if not attempt.image:
            continue

        try:
            with attempt.image.open("rb") as src:
                with open(filepath, "wb") as dst:
                    shutil.copyfileobj(src, dst)
            exported += 1
        except Exception as e:
            print(f"  Failed to export {attempt.id}: {e}")

    print(f"Exported {exported} images to {output_dir}")
