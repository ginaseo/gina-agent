import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from slack_sdk import WebClient

from ingest.base import BaseProvider

ROOT = Path(__file__).resolve().parents[2]
VAULT = ROOT / "HermesVault"

load_dotenv(ROOT / ".env")


class SlackProvider(BaseProvider):

    def __init__(self):
        self.client = None
        self.token = os.getenv("SLACK_BOT_TOKEN")
        # 콤마 구분 다채널 지원: SLACK_CHANNEL_IDS=C01,C02 또는 SLACK_CHANNEL_ID=C01
        ids = os.getenv("SLACK_CHANNEL_IDS") or os.getenv("SLACK_CHANNEL_ID", "")
        self.channels = [c.strip() for c in ids.split(",") if c.strip()]

    def process(self):
        self.run()

    def connect(self):
        self.client = WebClient(token=self.token)
        print("[Slack] Connected")

    def fetch(self):
        results = {}
        for ch in self.channels:
            try:
                resp = self.client.conversations_history(channel=ch, limit=20)
                results[ch] = resp["messages"]
            except Exception as e:
                print(f"[Slack] Failed to fetch {ch}: {e}")
        return results or None

    def save(self, data):
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        date = now.strftime("%Y-%m-%d")

        for ch, messages in data.items():
            vault = VAULT / "slack" / year / month
            vault.mkdir(parents=True, exist_ok=True)
            filename = vault / f"{date}-{ch}.md"

            with open(filename, "w", encoding="utf-8", newline="\n") as f:
                f.write(f"# Slack Import — {ch}\n\n")
                f.write(f"Date: {date}\n\n")
                f.write("---\n\n")

                for idx, msg in enumerate(reversed(messages), start=1):
                    text = msg.get("text", "").strip()
                    ts = msg.get("ts", "")
                    f.write(f"## Message {idx}\n\n")
                    f.write(f"Timestamp: {ts}\n\n")
                    f.write(text)
                    f.write("\n\n")
                    f.write("---\n\n")

            print(f"[Slack] Saved {filename.name}")
