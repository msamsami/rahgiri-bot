import re

from bot.models import TrackingRecord


def normalize_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s*\(مشاهده.*?\)", "", text)
    text = re.sub(r"،(?!\s)", "، ", text)
    text = re.sub(r"(?<=[\u0600-\u06FF])(\d+)(?=[\u0600-\u06FF])", r" \1 ", text)
    return text


def success_msg(msg: str) -> str:
    return "✅ " + msg


def error_msg(msg: str) -> str:
    return "❌ " + msg


def warning_msg(msg: str) -> str:
    return "⚠️ " + msg


def format_tracking_record(record: TrackingRecord) -> str:
    location = f"{record.location}\n" if record.location else ""
    return "\n".join([f"*{record.id}. {record.description}*", f"{location}{record.date} - {record.time}"])
