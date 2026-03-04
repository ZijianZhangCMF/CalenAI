#!/usr/bin/env python3
"""
CalenAI - 通过自然语言自动创建 macOS 日历事件
https://github.com/ZijianZhangCMF/CalenAI
"""

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
EXAMPLE_CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.example.json")


# ─── Config ──────────────────────────────────────────────────────────────────


def list_system_calendars():
    """通过 AppleScript 获取 macOS 日历列表"""
    try:
        r = subprocess.run(
            ["osascript", "-e", 'tell application "Calendar" to get name of every calendar'],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return [c.strip() for c in r.stdout.strip().split(",")]
    except Exception:
        pass
    return []


def interactive_setup():
    """首次运行引导：创建 config.json"""
    print("=" * 50)
    print("  CalenAI 首次配置向导")
    print("=" * 50)

    if os.path.exists(EXAMPLE_CONFIG_PATH):
        shutil.copy(EXAMPLE_CONFIG_PATH, CONFIG_PATH)
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {
            "api_url": "", "api_key": "", "model": "gpt-4o",
            "default_calendar": "", "calendars": [],
            "default_alert_minutes": 15,
        }

    print("\n[1/3] API 配置")
    print("  支持所有 OpenAI 兼容接口 (OpenAI / DeepSeek / Moonshot / Ollama 等)")
    url = input(f"  API 地址 [{config.get('api_url', '')}]: ").strip()
    if url:
        config["api_url"] = url

    key = input("  API 密钥: ").strip()
    if key:
        config["api_key"] = key

    model = input(f"  模型名称 [{config.get('model', 'gpt-4o')}]: ").strip()
    if model:
        config["model"] = model

    print("\n[2/3] 检测日历...")
    cals = list_system_calendars()
    if cals:
        user_cals = [c for c in cals if c not in ("生日", "中国大陆节假日", "计划的提醒事项")]
        print(f"  发现 {len(cals)} 个日历:")
        for i, c in enumerate(cals, 1):
            marker = " *" if c in user_cals else ""
            print(f"    {i}. {c}{marker}")
        config["calendars"] = user_cals if user_cals else cals[:1]
        default = user_cals[0] if user_cals else cals[0]
        choice = input(f"  默认日历 [{default}]: ").strip()
        config["default_calendar"] = choice if choice else default
    else:
        print("  未检测到日历（请先打开「日历」App 创建一个日历）")
        cal_name = input("  手动输入日历名称: ").strip()
        config["default_calendar"] = cal_name or "Calendar"
        config["calendars"] = [config["default_calendar"]]

    print("\n[3/3] 提醒设置")
    alert = input(f"  默认提前提醒分钟数 [{config.get('default_alert_minutes', 15)}]: ").strip()
    if alert.isdigit():
        config["default_alert_minutes"] = int(alert)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"\n✓ 配置已保存到 {CONFIG_PATH}")
    print("  之后可随时编辑该文件修改配置\n")
    return config


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return interactive_setup()

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    api_key = config.get("api_key", "")
    if not api_key or api_key in ("YOUR_API_KEY_HERE", "") or api_key.startswith("sk-xxxx"):
        print("错误: 请在 config.json 中填写有效的 api_key")
        print(f"  配置文件路径: {CONFIG_PATH}")
        sys.exit(1)

    if not config.get("calendars"):
        cals = list_system_calendars()
        if cals:
            user_cals = [c for c in cals if c not in ("生日", "中国大陆节假日", "计划的提醒事项")]
            config["calendars"] = user_cals if user_cals else cals[:1]
            if not config.get("default_calendar") or config["default_calendar"] not in cals:
                config["default_calendar"] = config["calendars"][0]
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                f.write("\n")

    return config


# ─── LLM ─────────────────────────────────────────────────────────────────────


def call_llm(config, user_input):
    now = datetime.now()
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    current_weekday = weekday_names[now.weekday()]

    calendars = config.get("calendars", [])
    default_cal = config.get("default_calendar", "Calendar")

    calendar_rule = ""
    if calendars:
        cal_list = "、".join(f"「{c}」" for c in calendars)
        calendar_rule = f"""7. 根据事件内容自动选择最合适的日历，可选: {cal_list}，默认「{default_cal}」"""

    system_prompt = f"""你是一个日程解析助手。当前时间: {now.strftime('%Y-%m-%d %H:%M')} {current_weekday}。

将用户的自然语言描述解析为 JSON 数组，每个元素格式：
{{
  "title": "事件标题",
  "start_date": "YYYY-MM-DD HH:MM",
  "end_date": "YYYY-MM-DD HH:MM",
  "location": "",
  "notes": "",
  "all_day": false,
  "calendar": "{default_cal}",
  "alert_minutes": {config.get('default_alert_minutes', 15)}
}}

规则：
1. 未指定结束时间 → 默认1小时
2. "全天"或无具体时间 → all_day:true, 00:00~23:59
3. 明天={（now + timedelta(days=1)).strftime('%Y-%m-%d')}，后天={(now + timedelta(days=2)).strftime('%Y-%m-%d')}
4. "下周X"基于当前{current_weekday}推算
5. location/notes 没提到则留空字符串
6. 只返回 JSON 数组，不要 markdown 包裹
{calendar_rule}"""

    api_url = config["api_url"].rstrip("/")
    if not api_url.endswith("/chat/completions"):
        api_url += "/chat/completions"

    payload = json.dumps({
        "model": config.get("model", "gpt-4o"),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        "temperature": 0.1,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
    }

    result = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(api_url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"API 错误 (HTTP {e.code}): {body}")
            sys.exit(1)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt < 2:
                print(f"  网络异常，重试中 ({attempt + 2}/3)...")
                time.sleep(2)
            else:
                print(f"网络错误（已重试3次）: {getattr(e, 'reason', e)}")
                sys.exit(1)

    content = result["choices"][0]["message"]["content"].strip()
    # 去除可能的 markdown 包裹
    for prefix in ("```json", "```"):
        if content.startswith(prefix):
            content = content[len(prefix):]
            break
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        events = json.loads(content)
    except json.JSONDecodeError:
        print(f"LLM 返回无法解析:\n{content}")
        sys.exit(1)

    if isinstance(events, dict):
        events = [events]
    return events


# ─── Calendar ────────────────────────────────────────────────────────────────


def create_calendar_event(event, calendar_name):
    start_dt = datetime.strptime(event["start_date"], "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(event["end_date"], "%Y-%m-%d %H:%M")

    def esc(s):
        return s.replace("\\", "\\\\").replace('"', '\\"')

    allday_prop = "allday event:true, " if event.get("all_day") else ""

    applescript = f'''
set startDate to current date
set year of startDate to {start_dt.year}
set month of startDate to {start_dt.month}
set day of startDate to {start_dt.day}
set hours of startDate to {start_dt.hour}
set minutes of startDate to {start_dt.minute}
set seconds of startDate to 0

set endDate to current date
set year of endDate to {end_dt.year}
set month of endDate to {end_dt.month}
set day of endDate to {end_dt.day}
set hours of endDate to {end_dt.hour}
set minutes of endDate to {end_dt.minute}
set seconds of endDate to 0

tell application "Calendar"
    tell calendar "{esc(calendar_name)}"
        set newEvent to make new event with properties {{summary:"{esc(event['title'])}", start date:startDate, end date:endDate, {allday_prop}location:"{esc(event.get('location', ''))}", description:"{esc(event.get('notes', ''))}"}}
        tell newEvent
            make new sound alarm at end of sound alarms with properties {{trigger interval:-{event.get('alert_minutes', 15)}}}
        end tell
    end tell
end tell
return "OK"
'''
    try:
        r = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0:
            print(f"  创建失败: {r.stderr.strip()}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print("  创建超时")
        return False


# ─── Main ────────────────────────────────────────────────────────────────────


def format_event(event):
    lines = [f"  标题: {event['title']}"]
    lines.append(f"  时间: {event['start_date']} → {event['end_date']}")
    if event.get("all_day"):
        lines.append("  全天事件")
    if event.get("location"):
        lines.append(f"  地点: {event['location']}")
    if event.get("notes"):
        lines.append(f"  备注: {event['notes']}")
    if event.get("calendar"):
        lines.append(f"  日历: {event['calendar']}")
    return "\n".join(lines)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        interactive_setup()
        return

    if len(sys.argv) < 2:
        print("CalenAI - 自然语言智能日程助手\n")
        print("用法:")
        print("  python3 calenai.py \"你的日程描述\"")
        print("  python3 calenai.py --setup          # 重新配置\n")
        print("示例:")
        print("  python3 calenai.py \"明天下午3点开会\"")
        print("  python3 calenai.py \"周五10点在会议室A评审，下周一全天出差\"")
        sys.exit(0)

    user_input = " ".join(sys.argv[1:])
    config = load_config()
    default_cal = config.get("default_calendar", "Calendar")

    print(f"正在解析: \"{user_input}\"\n")
    events = call_llm(config, user_input)

    print(f"解析出 {len(events)} 个日程:\n")
    success_count = 0
    for i, event in enumerate(events, 1):
        cal = event.get("calendar", default_cal)
        print(f"[{i}] {format_event(event)}")
        if create_calendar_event(event, cal):
            print(f"  ✓ 已添加到「{cal}」\n")
            success_count += 1
        else:
            print("  ✗ 添加失败\n")

    summary = f"完成: {success_count}/{len(events)} 个日程已创建"
    print(summary)

    if os.environ.get("SHORTCUT_MODE"):
        print(json.dumps({
            "success": success_count == len(events),
            "total": len(events),
            "created": success_count,
            "summary": summary,
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
