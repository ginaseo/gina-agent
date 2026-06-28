from pathlib import Path

from processor.log import get_logger
from processor.processing_state import ProcessingState

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "HermesVault"
RAW = VAULT / "slack"
KNOWLEDGE = VAULT / "knowledge" / "slack"

logger = get_logger(__name__)


class MarkdownProcessor:

    def __init__(self):
        self.force = False

    def process(self) -> None:
        KNOWLEDGE.mkdir(parents=True, exist_ok=True)

        state = ProcessingState("markdown", force=self.force)
        files = list(RAW.rglob("*.md"))

        if not files:
            logger.info("[INFO] No markdown files.")
            return

        if not any(state.is_modified(f) for f in files):
            for file in files:
                logger.info(f"[SKIP] {file.name}")
            logger.info("")
            logger.info("Processed : 0 file(s)")
            logger.info(f"Skipped  : {len(files)} file(s)")
            return

        generated = 0
        skipped = 0

        for file in files:
            if not state.is_modified(file):
                logger.info(f"[SKIP] {file.name}")
                skipped += 1
                continue

            content = file.read_text(encoding="utf-8")
            output = KNOWLEDGE / file.name
            output.write_text(
                "---\n"
                "source: slack\n"
                "provider: SlackProvider\n"
                "status: processed\n"
                f"original_file: {file.name}\n"
                "---\n\n"
                "# Summary\n\n"
                "> TODO\n\n"
                "# Original Content\n\n" + content,
                encoding="utf-8",
            )
            state.update(file)
            generated += 1
            logger.info(f"[PROCESS] {output.name}")

        state.save()
        logger.info("")
        logger.info(f"Processed : {generated} file(s)")
        logger.info(f"Skipped  : {skipped} file(s)")
