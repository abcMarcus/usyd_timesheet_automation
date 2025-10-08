import re
from datetime import datetime
from pathlib import Path


def text_file_to_csv(
    text_file: str | Path,
    subject_code: str,
    pay_code: str = "A02",
    topic: str = "UOSMAT DEV",
    year: int = datetime.now().year
):
    text_file = Path(text_file)
    output_dir = Path("csvs")
    output_dir.mkdir(exist_ok=True)

    log_text = text_file.read_text()

    date_pattern = re.compile(r"^(\d{1,2})/(\d{1,2})$")
    time_pattern = re.compile(r"(\d{1,2})(?::(\d{2}))?(am|pm)", re.I)
    duration_pattern = re.compile(r"\(([\d.]+)\)")

    lines = [line.strip() for line in log_text.splitlines() if line.strip()]
    current_date = None
    results = []

    for line in lines:
        date_match = date_pattern.match(line)
        if date_match:
            day, month = map(int, date_match.groups())
            current_date = datetime(year, month, day)
            continue

        time_match = time_pattern.search(line)
        dur_match = duration_pattern.search(line)
        if current_date and time_match and dur_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = time_match.group(3).lower()
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0

            duration_hours = dur_match.group(1)
            start_time = f"{hour:02d}:{minute:02d}"
            date_str = current_date.strftime("%d/%m/%Y")

            csv_line = (
                f"{date_str},{subject_code},{pay_code},{duration_hours},"
                f"{start_time},,,,,{topic},,,"
            )
            results.append(csv_line)

    output_path = output_dir / f"{text_file.stem}.csv"
    output_path.write_text("\n".join(results) + "\n")
    return output_path