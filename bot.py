import requests
import time
import json
import os

FACEIT_NICKNAMES = [
    nickname.strip()
    for nickname in os.environ["FACEIT_NICKNAMES"].split(",")
    if nickname.strip()
]

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CHECK_INTERVAL = 300
STATE_FILE = "/app/data/state.json"


def get_faceit_user_id(nickname):
    url = f"https://www.faceit.com/api/users/v1/nicknames/{nickname}"

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

    return user.get("verification_level", 0)


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
        return None

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=2
        )


def check_account(nickname, state):
    print(
        f"[FACEIT] Проверяю аккаунт {nickname}...",
        flush=True
    )

    user_id = get_faceit_user_id(nickname)

    print(
        f"[FACEIT] {nickname} | User ID: {user_id}",
        flush=True
    )

    verification_level = get_verification_status(user_id)

    print(
        f"[FACEIT] {nickname} | verification_level = "
        f"{verification_level}",
        flush=True
    )

    verified = verification_level > 0

    # Новый аккаунт в списке:
    # запоминаем его текущее состояние без уведомления.
    if nickname not in state:
        state[nickname] = {
            "verified": verified
        }

        print(
            f"[STATE] {nickname} | Первое добавление. "
            f"Состояние сохранено без уведомления.",
            flush=True
        )

        return

    previous_verified = state[nickname].get("verified", False)

    if verified:
        print(
            f"[FACEIT] {nickname} | ✅ Аккаунт верифицирован.",
            flush=True
        )

        # Только переход:
        # НЕ ВЕРИФИЦИРОВАН → ВЕРИФИЦИРОВАН
        if not previous_verified:
            message = (
                "🎉 FACEIT\n\n"
                f"Аккаунт {nickname} успешно "
                "верифицирован! ✅"
            )

            print(
                f"[TELEGRAM] {nickname} | Отправляю уведомление...",
                flush=True
            )

            send_telegram_message(message)

            print(
                f"[TELEGRAM] {nickname} | ✅ Уведомление отправлено.",
                flush=True
            )
        else:
            print(
                f"[TELEGRAM] {nickname} | Уведомление уже отправлялось.",
                flush=True
            )

    else:
        print(
            f"[FACEIT] {nickname} | ⏳ Ещё не верифицирован.",
            flush=True
        )

    state[nickname]["verified"] = verified


print("==========================================", flush=True)
print("FACEIT Verification Bot", flush=True)
print("==========================================", flush=True)
print(
    f"Аккаунтов для проверки: {len(FACEIT_NICKNAMES)}",
    flush=True
)

for nickname in FACEIT_NICKNAMES:
    print(f"  • {nickname}", flush=True)

print("Проверка каждые 5 минут.", flush=True)
print("==========================================", flush=True)


while True:
    state = load_state()

    # Первый запуск
    if state is None:
        state = {}

    for nickname in FACEIT_NICKNAMES:
        try:
            check_account(nickname, state)

        except Exception as e:
            print(
                f"[ERROR] {nickname} | {repr(e)}",
                flush=True
            )

    save_state(state)

    print(
        f"Следующая проверка через "
        f"{CHECK_INTERVAL // 60} минут...",
        flush=True
    )

    time.sleep(CHECK_INTERVAL)
