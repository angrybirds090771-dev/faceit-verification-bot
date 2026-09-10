import requests
import time
import json
import os

FACEIT_NICKNAME = os.environ["FACEIT_NICKNAME"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CHECK_INTERVAL = 300
STATE_FILE = "/app/data/state.json"


def get_faceit_user_id():
    url = f"https://www.faceit.com/api/users/v1/nicknames/{FACEIT_NICKNAME}"

    response = requests.get(
        url,
        headers={
            "Accept": "application/json, text/plain, */*"
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return data["payload"]["id"]


def get_verification_status(user_id):
    url = "https://www.faceit.com/api/user-summary/v2/list"

    response = requests.post(
        url,
        json={
            "ids": [user_id]
        },
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*"
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    user = data["payload"][user_id]

    verification_level = user.get("verification_level", 0)

    return verification_level


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text
        },
        timeout=30
    )

    response.raise_for_status()


def load_state():
    if not os.path.exists(STATE_FILE):
        return {
            "verified": False,
            "notification_sent": False
        }

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "verified": False,
            "notification_sent": False
        }


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=2
        )


def check_verification():
    state = load_state()

    print(
        f"[FACEIT] Проверяю аккаунт {FACEIT_NICKNAME}...",
        flush=True
    )

    user_id = get_faceit_user_id()

    print(
        f"[FACEIT] User ID: {user_id}",
        flush=True
    )

    verification_level = get_verification_status(user_id)

    print(
        f"[FACEIT] verification_level = {verification_level}",
        flush=True
    )

    verified = verification_level > 0

    if verified:
        print(
            "[FACEIT] ✅ Аккаунт верифицирован.",
            flush=True
        )

        if not state["notification_sent"]:
            message = (
                "🎉 FACEIT\n\n"
                f"Аккаунт {FACEIT_NICKNAME} успешно "
                "верифицирован! ✅"
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


print("==========================================", flush=True)
print("FACEIT Verification Bot", flush=True)
print("==========================================", flush=True)
print(f"Аккаунт: {FACEIT_NICKNAME}", flush=True)
print("Проверка каждые 5 минут.", flush=True)
print("==========================================", flush=True)


while True:
    try:
        check_verification()

    except Exception as e:
        print(
            f"[ERROR] {repr(e)}",
            flush=True
        )

    print(
        f"Следующая проверка через "
        f"{CHECK_INTERVAL // 60} минут...",
        flush=True
    )

    time.sleep(CHECK_INTERVAL)
