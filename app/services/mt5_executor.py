import MetaTrader5 as mt5
import subprocess
import time

MT5_TERMINAL_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"


def ensure_mt5_terminal_running():
    try:
        subprocess.Popen(
            [MT5_TERMINAL_PATH],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)
    except Exception:
        pass

def resolve_symbol(requested_symbol: str):
    requested = requested_symbol.strip().upper()

    # 1. exact match first
    exact = mt5.symbol_info(requested)
    if exact is not None:
        return requested

    # 2. search all broker symbols for close match
    all_symbols = mt5.symbols_get()
    if not all_symbols:
        return None

    candidates = []
    for sym in all_symbols:
        name = sym.name.upper()

        # exact base contained in broker symbol, e.g. XAUUSDm / XAUUSD.pro / XAUUSD.a
        if name == requested:
            return sym.name

        if name.startswith(requested) or requested in name:
            candidates.append(sym.name)

    if candidates:
        # shortest candidate usually best, e.g. prefer XAUUSDm over XAUUSDmicrotest
        candidates.sort(key=len)
        return candidates[0]

    return None

def execute_trade(mt_login, mt_password, mt_server, symbol, action, lot, sl, tp):
    try:
        mt5.shutdown()
        time.sleep(1)

        ensure_mt5_terminal_running()
        time.sleep(2)

        if not mt5.initialize(path=MT5_TERMINAL_PATH):
            return {
                "success": False,
                "error": f"Init failed: {mt5.last_error()}"
            }

        authorized = mt5.login(
            login=int(mt_login),
            password=mt_password,
            server=mt_server
        )

        if not authorized:
            mt5.shutdown()
            time.sleep(2)

            ensure_mt5_terminal_running()
            time.sleep(2)

            if not mt5.initialize(path=MT5_TERMINAL_PATH):
                return {
                    "success": False,
                    "error": f"Init failed after retry: {mt5.last_error()}"
                }

            authorized = mt5.login(
                login=int(mt_login),
                password=mt_password,
                server=mt_server
            )

            if not authorized:
                return {
                    "success": False,
                    "error": f"Login failed: {mt5.last_error()}"
                }

        account = mt5.account_info()
        if account is None:
            return {
                "success": False,
                "error": "No account info after login"
            }

        broker_symbol = resolve_symbol(symbol)
        if broker_symbol is None:
            return {
                "success": False,
                "error": f"Symbol not found on broker: {symbol}"
            }

        symbol_info = mt5.symbol_info(broker_symbol)
        if symbol_info is None:
            return {
                "success": False,
                "error": f"Broker symbol info missing: {broker_symbol}"
            }

        if not symbol_info.visible:
            if not mt5.symbol_select(broker_symbol, True):
                return {
                    "success": False,
                    "error": f"Could not select broker symbol: {broker_symbol}"
                }

        tick = mt5.symbol_info_tick(broker_symbol)
        if tick is None:
            return {
                "success": False,
                "error": f"No tick data for broker symbol: {broker_symbol}"
            }

        action_lower = str(action).lower()
        if action_lower == "buy":
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        elif action_lower == "sell":
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            return {
                "success": False,
                "error": f"Invalid action: {action}"
            }

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": broker_symbol,
            "volume": float(lot),
            "type": order_type,
            "price": price,
            "sl": float(sl) if sl is not None else 0.0,
            "tp": float(tp) if tp is not None else 0.0,
            "deviation": 20,
            "magic": 123456,
            "comment": "NolimitzBots",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result is None:
            return {
                "success": False,
                "error": f"order_send returned None: {mt5.last_error()}"
            }

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {
                "success": False,
                "error": f"Trade failed retcode={result.retcode}"
            }

        return {
            "success": True,
            "message": f"Trade executed on {broker_symbol}",
            "order": result.order,
        }

    finally:
        mt5.shutdown()
        time.sleep(1)