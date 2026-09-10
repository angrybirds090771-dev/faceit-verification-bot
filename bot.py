import requests
import time
import json
import os

from playwright.sync_api import sync_playwright


# ==========================================
# НАСТРОЙКИ
# ==========================================

FACEIT_NICKNAME = os.environ["FACEIT_NICKNAME"]

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CHECK_INTERVAL = 300  # 5 минут

STATE_FILE = "state.json"


# ==========================================
# TELEGRAM
# ==========================================

def send_telegram_message(text):

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }

    response = requests.post(
        url,
        data=data,
        timeout=20
    )

    response.raise_for_status()


# ==========================================
# СОСТОЯНИЕ
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
# ПРОВЕРКА FACEIT BADGE
# ==========================================

def check_faceit_verification():

    url = (
        f"https://www.faceit.com/en/players/"
        f"{FACEIT_NICKNAME}"
    )

    print(
        f"[FACEIT] Открываю профиль: "
        f"{FACEIT_NICKNAME}"
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
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

            verification_icon = page.locator(
                '[data-testid="verification-icon"]'
            )

            count = verification_icon.count()

            verified = count > 0

            print(
                f"[FACEIT] {FACEIT_NICKNAME} | "
                f"verification icons = {count}"
            )

            print(
                f"[FACEIT] verified = {verified}"
            )

            return verified

        finally:

            browser.close()


# ==========================================
# ОСНОВНАЯ ПРОВЕРКА
# ==========================================

def check_verification():

    state = load_state()

    verified = check_faceit_verification()

    if verified:

        print(
            "[FACEIT] ✅ Аккаунт "
            "верифицирован."
        )

        if not state["notification_sent"]:

            message = (
                "🎉 FACEIT\n\n"
                f"Аккаунт {FACEIT_NICKNAME} "
                "успешно верифицирован! ✅"
            )

            print(
                "[TELEGRAM] Отправляю "
                "уведомление..."
            )

            send_telegram_message(
                message
            )

            state["notification_sent"] = True

            print(
                "[TELEGRAM] ✅ Уведомление "
                "отправлено."
            )

        else:

            print(
                "[TELEGRAM] Уведомление уже "
                "было отправлено."
            )

    else:

        print(
            "[FACEIT] ⏳ Аккаунт ещё "
            "не верифицирован."
        )

        state["notification_sent"] = False

    state["verified"] = verified

    save_state(state)


# ==========================================
# ЗАПУСК
# ==========================================

print()
print("==========================================")
print("FACEIT Verification Bot")
print("==========================================")
print(
    f"Аккаунт: {FACEIT_NICKNAME}"
)
print(
    "Проверка каждые 5 минут."
)
print("==========================================")
print()


while True:

    try:

        check_verification()

    except Exception as e:

        print(
            "[ERROR]",
            repr(e)
        )

    print()
    print(
        f"Следующая проверка через "
        f"{CHECK_INTERVAL // 60} минут..."
    )
    print()

    time.sleep(
        CHECK_INTERVAL
    )
