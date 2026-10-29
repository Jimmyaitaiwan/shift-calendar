#!/usr/bin/env python3
"""產生 shift.ics（班表訂閱行事曆）

輸入：shifts.csv，每行「日期,班別,上班時間[,下班時間]」，例如
    2026-11-01,早班,08:00,16:00
    2026-11-02,休假
規則：
  - 上班日建「有時間的活動」（從上班時間開始），提醒固定在前一晚 21:00
    （iOS 對有時間的活動預設不加提示，不會再多出當天的提醒）
  - 休假建當天 08:00 的活動，同樣前一晚 21:00 提醒
  - 標題格式：MM/DD（週）班別 HH:MM 上班
"""
import csv, sys
from datetime import datetime, timedelta, timezone

TZ = timezone(timedelta(hours=8))
WEEK = "一二三四五六日"
REMIND_HOUR = 21

def utc(dt):
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def main(src="shifts.csv", out="shift.ics"):
    now = utc(datetime.now(TZ))
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Shift Reminder//ZH-TW",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "X-WR-CALNAME:上班班表",
             "X-WR-TIMEZONE:Asia/Taipei"]
    for row in csv.reader(open(src, encoding="utf-8")):
        row = [c.strip() for c in row if c.strip()]
        if not row or row[0].startswith("#"):
            continue
        day = datetime.strptime(row[0], "%Y-%m-%d").replace(tzinfo=TZ)
        shift = row[1]
        label = f"{day:%m/%d}（{WEEK[day.weekday()]}）"
        if len(row) >= 3:
            h, m = map(int, row[2].split(":"))
            start = day.replace(hour=h, minute=m)
            title = f"{label}{shift} {row[2]} 上班"
            if len(row) >= 4:
                eh, em = map(int, row[3].split(":"))
                end = day.replace(hour=eh, minute=em)
                if end <= start:
                    end += timedelta(days=1)
            else:
                end = start + timedelta(hours=1)
        else:  # 休假等沒有上班時間的日子
            start = day.replace(hour=8)
            end = start + timedelta(minutes=30)
            title = f"{label}{shift}"
        remind = (day - timedelta(days=1)).replace(hour=REMIND_HOUR)
        mins = int((start - remind).total_seconds() // 60)
        lines += ["BEGIN:VEVENT",
                  f"UID:shift-{day:%Y%m%d}@shift-reminder",
                  f"DTSTAMP:{now}",
                  f"DTSTART:{utc(start)}",
                  f"DTEND:{utc(end)}",
                  f"SUMMARY:{title}",
                  f"DESCRIPTION:{title}",
                  "TRANSP:TRANSPARENT",
                  "BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{title}",
                  f"TRIGGER:-PT{mins // 60}H{mins % 60}M", "END:VALARM",
                  "END:VEVENT"]
    lines.append("END:VCALENDAR")
    open(out, "w", encoding="utf-8", newline="").write("\r\n".join(lines) + "\r\n")

if __name__ == "__main__":
    main(*sys.argv[1:])
