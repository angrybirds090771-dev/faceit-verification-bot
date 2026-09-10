import requests
import time
import json
import os
import subprocess
import platform

from playwright.sync_api import sync_playwright


# ==========================================
# НАСТРОЙКИ
# ==========================================

FACEIT_NICKNAME = os.environ["FACEIT_NICKNAME"]

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CHECK_INTERVAL = 300

STATE_FILE = "state.json"


# ==========================================
# LINUX / XVFB
# ==========================================

xvfb_process = None

if platform.system() == "Linux":

    print("[SYSTEM] Запускаю Xvfb...", flush=True)

    xvfb_process = subprocess.Popen(
        [
            "Xvfb",
            ":99",
            "-screen",
            "0",
            "1920x1080x24",
            "-ac"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    os.environ["DISPLAY"] = ":99"

    time.sleep(2)

    print(
        "[SYSTEM] Xvfb запущен. DISPLAY=:99",
        flush=True
    )


# ==========================================
# TELEGRAM
# ==========================================

def send_telegram_message(text):

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text
        },
        timeout=20
    )

    response.raise_for_status()


# ==========================================
# STATE
# ==========================================

def load_state():

    if not os.path.exists(STATE_FILE):

        return {
            "verified": False,
            "notification_sent": False
        }

    with open(
        STATE_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def save_state(state):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=2
        )


# ==========================================
# FACEIT VERIFICATION BADGE
# ==========================================

def check_faceit_verification():

    url = (
        f"https://www.faceit.com/en/players/"
        f"{FACEIT_NICKNAME}"
    )

    print(
        f"[FACEIT] Открываю профиль: "
        f"{FACEIT_NICKNAME}",
        flush=True
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-dev-shm-usage"
            ]
        )

        page = browser.new_page(
            viewport={
                "width": 1920,
                "height": 1080
            }
        )

        try:

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(10000)

            badge = page.locator(
                '[data-testid="verification-icon"]'
            )

            count = badge.count()

            verified = count > 0

            print(
                f"[FACEIT] {FACEIT_NICKNAME} | "
                f"verification icons = {count}",
                flush=True
            )

            print(
                f"[FACEIT] verified = {verified}",
                flush=True
            )

            return verified

        finally:

            browser.close()


# ==========================================
# ПРОВЕРКА
# ==========================================

def check_verification():

    state = load_state()

    verified = check_faceit_verification()

    if verified:

        print(
            "[FACEIT] ✅ Аккаунт верифицирован.",
            flush=True
        )

        if not state["notification_sent"]:

            message = (
                "🎉 FACEIT\n\n"
                f"Аккаунт {FACEIT_NICKNAME} "
                "успешно верифицирован! ✅"
            )

            print(
                "[TELEGRAM] Отправляю уведомление...",
                flush=True
            )

            send_telegram_message(message)

            state["notification_sent"] = True

            print(
                "[TELEGRAM] ✅ Уведомление отправлено.",
                flush=True
            )

        else:

            print(
                "[TELEGRAM] Уведомление уже отправлялось.",
                flush=True
            )

    else:

        print(
            "[FACEIT] ⏳ Аккаунт ещё не верифицирован.",
            flush=True
        )

        state["notification_sent"] = False

    state["verified"] = verified

    save_state(state)


# ==========================================
# START
# ==========================================

print(
    "==========================================",
    flush=True
)

print(
    "FACEIT Verification Bot",
    flush=True
)

print(
    "==========================================",
    flush=True
)

print(
    f"Аккаунт: {FACEIT_NICKNAME}",
    flush=True
)

print(
    "Проверка каждые 5 минут.",
    flush=True
)

print(
    "==========================================",
    flush=True
)


while True:

    try:

        check_verification()

    except Exception as e:

        print(
            "[ERROR]",
            repr(e),
            flush=True
        )

    print(
        f"Следующая проверка через "
        f"{CHECK_INTERVAL // 60} минут...",
        flush=True
    )

    time.sleep(CHECK_INTERVAL)
