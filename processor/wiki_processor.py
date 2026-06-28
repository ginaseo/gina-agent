from pathlib import Path

from processor.log import get_logger
from processor.processing_state import ProcessingState

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "HermesVault"
INPUT = VAULT / "knowledge" / "slack"
OUTPUT = VAULT / "wiki" / "slack"

logger = get_logger(__name__)


class WikiProcessor:

    def __init__(self):
        self.force = False

    def process(self) -> None:
        OUTPUT.mkdir(parents=True, exist_ok=True)

        state = ProcessingState("wiki", force=self.force)
        files = list(INPUT.glob("*.md"))

        if not files:
            logger.info("[INFO] No markdown files.")
            return

        if not any(state.is_modified(f) for f in files):
            for file in files:
                logger.info(f"[SKIP] {file.name}")
            logger.info("")
            logger.info("Generated : 0 wiki file(s)")
            logger.info(f"Skipped  : {len(files)} wiki file(s)")
            return

        generated = 0
        skipped = 0

        for file in files:
            if not state.is_modified(file):
                logger.info(f"[SKIP] {file.name}")
                skipped += 1
                continue

            output = OUTPUT / file.name
            output.write_text(file.read_text(encoding="utf-8"), encoding="utf-8")
            state.update(file)
            generated += 1
            logger.info(f"[WIKI] {output.name}")

        state.save()
        logger.info("")
        logger.info(f"Generated : {generated} wiki file(s)")
        logger.info(f"Skipped  : {skipped} wiki file(s)")
