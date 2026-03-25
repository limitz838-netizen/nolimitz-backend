import time
from datetime import datetime, timezone
from typing import Optional

import requests
import MetaTrader5 as mt5

# =========================
# SETTINGS
# =========================
LICENSE_KEY = "NL-4B72F9125A"
BACKEND_URL = "http://127.0.0.1:8001"
POLL_INTERVAL = 2
EXECUTE_TRADES = True

# Only execute signals created after the bridge starts
BRIDGE_STARTED_AT = datetime.now(timezone.utc)

# Optional freshness rule:
# only allow signals newer than this many seconds
MAX_SIGNAL_AGE_SECONDS = 15

# Prevent duplicate execution in one bridge session
executed_signal_ids = set()


def parse_signal_time(signal: dict) -> Optional[datetime]:
    created_at = signal.get("created_at")
    if not created_at:
        return None

    try:
        # Handles "...Z" and timezone strings
        created_at = created_at.replace("Z", "+00:00")
        dt = datetime.fromisoformat(created_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def connect_mt5() -> bool:
    if not mt5.initialize():
        print("❌ MT5 initialize failed:", mt5.last_error())
        return False

    account = mt5.account_info()
    if account is None:
        print("❌ MT5 connected, but no account is logged in.")
        return False

    print("✅ MT5 connected")
    print("Account login:", account.login)
    print("Server:", account.server)
    print("Balance:", account.balance)
    return True


def fetch_signals():
    url = f"{BACKEND_URL}/client/signals/{LICENSE_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print("❌ Failed to fetch signals:", e)
        return []


def symbol_exists(symbol: str) -> bool:
    info = mt5.symbol_info(symbol)
    if info is None:
        print(f"❌ Symbol not found in MT5: {symbol}")
        return False

    if not info.visible:
        if not mt5.symbol_select(symbol, True):
            print(f"❌ Failed to enable symbol: {symbol}")
            return False

    return True


def validate_stops(symbol: str, action: str, price: float, stop_loss, take_profit):
    info = mt5.symbol_info(symbol)
    if info is None:
        return False, "Symbol info not found"

    point = info.point
    stops_level = info.trade_stops_level or 0
    min_distance = stops_level * point

    if action == "buy":
        if stop_loss and stop_loss >= price:
            return False, "Buy SL must be below current price"
        if take_profit and take_profit <= price:
            return False, "Buy TP must be above current price"
        if stop_loss and (price - stop_loss) < min_distance:
            return False, f"Buy SL too close. Minimum distance: {min_distance}"
        if take_profit and (take_profit - price) < min_distance:
            return False, f"Buy TP too close. Minimum distance: {min_distance}"

    elif action == "sell":
        if stop_loss and stop_loss <= price:
            return False, "Sell SL must be above current price"
        if take_profit and take_profit >= price:
            return False, "Sell TP must be below current price"
        if stop_loss and (stop_loss - price) < min_distance:
            return False, f"Sell SL too close. Minimum distance: {min_distance}"
        if take_profit and (price - take_profit) < min_distance:
            return False, f"Sell TP too close. Minimum distance: {min_distance}"

    return True, "OK"


def execute_trade(signal: dict):
    signal_id = signal.get("id")
    symbol = signal.get("symbol")
    action = str(signal.get("action", "")).lower()
    stop_loss = signal.get("stop_loss")
    take_profit = signal.get("take_profit")

    if not symbol_exists(symbol):
        return

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"❌ No tick data for {symbol}")
        return

    if action == "buy":
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
    elif action == "sell":
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
    else:
        print(f"❌ Invalid action: {action}")
        return

    is_valid, reason = validate_stops(symbol, action, price, stop_loss, take_profit)
    if not is_valid:
        print(f"❌ Signal {signal_id} skipped: {reason}")
        return

    lot_size = 0.01

    request_data = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": stop_loss if stop_loss else 0.0,
        "tp": take_profit if take_profit else 0.0,
        "deviation": 20,
        "magic": 123456,
        "comment": "NolimitzBots",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request_data)

    if result is None:
        print("❌ order_send returned None")
        print("Last error:", mt5.last_error())
        return

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("❌ Trade failed")
        print("Retcode:", result.retcode)
        print("Comment:", result.comment)
        return

    executed_signal_ids.add(signal_id)
    print(f"✅ Trade executed: {action.upper()} {symbol} at {price}")


def should_execute_signal(signal: dict) -> bool:
    signal_id = signal.get("id")
    if signal_id in executed_signal_ids:
        return False

    signal_time = parse_signal_time(signal)
    if signal_time is None:
        print(f"⚠️ Signal {signal_id} has no valid created_at. Skipping.")
        return False

    # Ignore any signal created before this bridge session started
    if signal_time < BRIDGE_STARTED_AT:
        return False

    # Ignore stale signals
    age_seconds = (datetime.now(timezone.utc) - signal_time).total_seconds()
    if age_seconds > MAX_SIGNAL_AGE_SECONDS:
        print(f"⚠️ Signal {signal_id} too old ({int(age_seconds)}s). Skipping.")
        return False

    return True


def main():
    if not connect_mt5():
        return

    print("🚀 Nolimitz MT5 Bridge started")
    print("Execution mode:", "LIVE" if EXECUTE_TRADES else "READ ONLY")
    print("Bridge started at (UTC):", BRIDGE_STARTED_AT.isoformat())

    try:
        while True:
            signals = fetch_signals()

            live_signals = [s for s in signals if should_execute_signal(s)]

            if live_signals:
                print(f"\n📥 Received {len(live_signals)} live signal(s)")
            else:
                print("\nNo live signals found")

            for signal in live_signals:
                print("----- NEW LIVE SIGNAL -----")
                print("ID:", signal.get("id"))
                print("Symbol:", signal.get("symbol"))
                print("Action:", signal.get("action"))
                print("Entry:", signal.get("entry_price"))
                print("SL:", signal.get("stop_loss"))
                print("TP:", signal.get("take_profit"))
                print("Status:", signal.get("status"))
                print("Created At:", signal.get("created_at"))

                if EXECUTE_TRADES:
                    execute_trade(signal)

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n🛑 Bridge stopped by user")
    finally:
        mt5.shutdown()
        print("MT5 shutdown complete")


if __name__ == "__main__":
    main()