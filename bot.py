import requests
import time
import json
import os

# ==========================================
# НАСТРОЙКИ
# ==========================================

FACEIT_API_KEY = os.environ["FACEIT_API_KEY"]
FACEIT_NICKNAME = os.environ["FACEIT_NICKNAME"]

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CHECK_INTERVAL = 300  # проверка каждые 5 минут

STATE_FILE = "state.json"


# ==========================================
# FACEIT
# ==========================================

def get_faceit_player():

    # 1. Находим игрока по никнейму
    search_url = "https://open.faceit.com/data/v4/search/players"

    headers = {
        "Authorization": f"Bearer {FACEIT_API_KEY}"
    }

    params = {
        "nickname": FACEIT_NICKNAME,
        "limit": 20
    }

    response = requests.get(
        search_url,
        headers=headers,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    players = data.get("items", [])

    player_id = None

    for player in players:

        if player.get(
            "nickname",
            ""
        ).lower() == FACEIT_NICKNAME.lower():

            player_id = player.get("player_id")
            break

    if not player_id:
        raise Exception(
            f"Игрок {FACEIT_NICKNAME} не найден"
        )

    # 2. Получаем полную информацию об игроке
    player_url = (
        f"https://open.faceit.com/data/v4/players/"
        f"{player_id}"
    )

    response = requests.get(
        player_url,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    return response.json()


# ==========================================
# TELEGRAM
# ==========================================

def send_telegram_message(text):

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
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
# СОХРАНЕНИЕ СОСТОЯНИЯ
# ==========================================

def load_state():

    if not os.path.exists(STATE_FILE):
        return {
            "verified": False,
            "notification_sent": False
        }

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except:
        return {
            "verified": False,
            "notification_sent": False
        }


def save_state(state):

    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, indent=4)


# ==========================================
# ПРОВЕРКА ВЕРИФИКАЦИИ
# ==========================================

def check_verification():

    try:

        player = get_faceit_player()

        nickname = player.get(
            "nickname",
            FACEIT_NICKNAME
        )

        verified = player.get(
            "verified",
            False
        )

        state = load_state()

        print(
            f"[FACEIT] {nickname} | "
            f"verified = {verified}"
        )

        # ==================================
        # АККАУНТ УЖЕ ВЕРИФИЦИРОВАН
        # ==================================

        if verified:

            # Если уведомление ещё не отправляли
            if not state["notification_sent"]:

                message = (
                    "🎉 FACEIT\n\n"
                    f"Аккаунт {nickname} "
                    "успешно верифицирован! ✅"
                )

                send_telegram_message(message)

                state["verified"] = True
                state["notification_sent"] = True

                save_state(state)

                print(
                    "🔔 Уведомление отправлено!"
                )

            else:

                print(
                    "✅ Уже уведомляли. "
                    "Новое сообщение не отправляем."
                )

        # ==================================
        # АККАУНТ ЕЩЁ НЕ ВЕРИФИЦИРОВАН
        # ==================================

        else:

            print(
                "⏳ Аккаунт ещё не верифицирован."
            )

            state["verified"] = False

            save_state(state)

    except Exception as error:

        print(
            f"❌ Ошибка: {error}"
        )


# ==========================================
# ЗАПУСК
# ==========================================

print("================================")
print(" FACEIT Verification Bot")
print("================================")
print()
print(
    f"Аккаунт: {FACEIT_NICKNAME}"
)
print(
    "Проверка каждые 5 минут."
)
print()

while True:

    check_verification()

    print(
        "Следующая проверка через "
        "5 минут..."
    )

    print()

    time.sleep(CHECK_INTERVAL)
