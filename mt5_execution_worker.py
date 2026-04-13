import time
from datetime import datetime, timezone
from typing import Optional

import MetaTrader5 as mt5
import requests

BACKEND_URL = "https://api.nolimitzpro.top"
POLL_SECONDS = 5
CLAIM_LIMIT = 10
MAX_OPEN_EVENT_AGE_SECONDS = 60
WORKER_MAGIC = 20260401

# CHANGE THIS to your real MT5 terminal path
MT5_TERMINAL_PATH = r"C:\Users\user\Desktop\NolimitzMT5Verifier\terminal64.exe"


# =========================
# TIME HELPERS
# =========================
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def is_stale_open_execution(execution: dict) -> bool:
    if execution.get("event_type") != "open":
        return False

    created_at = execution.get("created_at")
    if not created_at:
        return False

    dt = parse_iso_datetime(created_at)
    age = (utc_now() - dt).total_seconds()
    return age > MAX_OPEN_EVENT_AGE_SECONDS


# =========================
# BACKEND HELPERS
# =========================
def backend_claim_pending_executions():
    res = requests.post(
        f"{BACKEND_URL}/copier/executions/claim",
        params={"limit": CLAIM_LIMIT},
        timeout=30,
    )
    res.raise_for_status()
    return res.json()


def backend_get_execution_account(execution_id: int):
    res = requests.get(
        f"{BACKEND_URL}/copier/executions/{execution_id}/account",
        timeout=30,
    )
    res.raise_for_status()
    return res.json()


def backend_update_execution(
    execution_id: int,
    status: str,
    client_ticket: Optional[str] = None,
    error_message: Optional[str] = None,
):
    payload = {
        "status": status,
        "client_ticket": str(client_ticket) if client_ticket is not None else None,
        "error_message": error_message,
    }
    res = requests.post(
        f"{BACKEND_URL}/copier/executions/{execution_id}/update",
        json=payload,
        timeout=30,
    )
    res.raise_for_status()
    return res.json()


def backend_get_client_symbol_settings(license_key: str):
    payload = {"license_key": license_key}
    res = requests.post(
        f"{BACKEND_URL}/client/symbols/list",
        json=payload,
        timeout=30,
    )
    res.raise_for_status()
    return res.json()


def backend_get_ticket_maps_by_keys(license_id: int, ea_id: int, master_ticket: str):
    res = requests.get(
        f"{BACKEND_URL}/copier/ticket-maps/by-keys",
        params={
            "license_id": license_id,
            "ea_id": ea_id,
            "master_ticket": master_ticket,
        },
        timeout=30,
    )

    if res.status_code == 404:
        return []

    res.raise_for_status()
    return res.json()


def backend_get_open_ticket_maps_by_keys(license_id: int, ea_id: int, master_ticket: str):
    res = requests.get(
        f"{BACKEND_URL}/copier/ticket-maps/by-keys/all-open",
        params={
            "license_id": license_id,
            "ea_id": ea_id,
            "master_ticket": master_ticket,
        },
        timeout=30,
    )
    res.raise_for_status()
    return res.json()


def backend_upsert_ticket_map(
    execution: dict,
    client_ticket: str,
    is_open: bool = True,
    manually_closed: bool = False,
    child_ticket_index: int = 1,
):
    payload = {
        "license_id": execution["license_id"],
        "ea_id": execution["ea_id"],
        "master_ticket": execution["master_ticket"],
        "client_ticket": str(client_ticket),
        "child_ticket_index": child_ticket_index,
        "symbol": execution["symbol"],
        "action": execution.get("action"),
        "is_open": is_open,
        "manually_closed": manually_closed,
    }

    res = requests.post(
        f"{BACKEND_URL}/copier/ticket-maps/upsert",
        json=payload,
        timeout=30,
    )
    res.raise_for_status()
    return res.json()


def backend_mark_ticket_map_closed(
    execution: dict,
    manually_closed: bool = False,
):
    payload = {
        "license_id": execution["license_id"],
        "ea_id": execution["ea_id"],
        "master_ticket": execution["master_ticket"],
        "manually_closed": manually_closed,
    }
    res = requests.post(
        f"{BACKEND_URL}/copier/ticket-maps/mark-closed",
        json=payload,
        timeout=30,
    )
    res.raise_for_status()
    return res.json()


# =========================
# MT5 HELPERS
# =========================
def initialize_and_login(mt_login: str, mt_password: str, mt_server: str):
    if not mt5.initialize(path=MT5_TERMINAL_PATH):
        raise Exception(f"MT5 initialize failed: {mt5.last_error()}")

    authorized = mt5.login(
        login=int(mt_login),
        password=mt_password,
        server=mt_server,
    )
    if not authorized:
        raise Exception(f"MT5 login failed: {mt5.last_error()}")


def shutdown_mt5():
    try:
        mt5.shutdown()
    except Exception:
        pass


def find_broker_symbol(requested_symbol: str) -> str:
    requested = requested_symbol.upper().strip()
    symbols = mt5.symbols_get()

    if not symbols:
        raise Exception("No broker symbols returned from MT5")

    all_names = [s.name for s in symbols]

    for name in all_names:
        if name.upper() == requested:
            return name

    for name in all_names:
        upper_name = name.upper()

        if upper_name.startswith(requested):
            return name
        if upper_name.endswith(requested):
            return name
        if requested in upper_name:
            return name

    if requested in ["XAUUSD", "XAUUSDM"]:
        gold_candidates = []
        for name in all_names:
            upper_name = name.upper()
            if "XAUUSD" in upper_name or "GOLD" in upper_name:
                gold_candidates.append(name)

        if gold_candidates:
            return gold_candidates[0]

    raise Exception(f"Symbol not found on broker for requested symbol: {requested_symbol}")


def ensure_symbol_ready(symbol: str):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        raise Exception(f"Mapped symbol not found: {symbol}")

    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            raise Exception(f"Failed to select symbol: {symbol}")

    return symbol_info


def count_open_positions_for_symbol(broker_symbol: str) -> int:
    positions = mt5.positions_get(symbol=broker_symbol)
    if not positions:
        return 0
    return len(positions)


def mapped_ticket_still_open(account: dict, client_ticket: str) -> bool:
    initialize_and_login(
        mt_login=account["mt_login"],
        mt_password=account["mt_password"],
        mt_server=account["mt_server"],
    )

    try:
        positions = mt5.positions_get(ticket=int(client_ticket))
        return bool(positions)
    finally:
        shutdown_mt5()


def get_open_mapped_tickets_for_execution(account: dict, execution: dict) -> list[dict]:
    mappings = backend_get_open_ticket_maps_by_keys(
        license_id=execution["license_id"],
        ea_id=execution["ea_id"],
        master_ticket=execution["master_ticket"],
    )

    if not mappings:
        return []

    alive_mappings: list[dict] = []

    initialize_and_login(
        mt_login=account["mt_login"],
        mt_password=account["mt_password"],
        mt_server=account["mt_server"],
    )

    try:
        for mapping in mappings:
            client_ticket = mapping.get("client_ticket")
            if not client_ticket:
                continue

            positions = mt5.positions_get(ticket=int(client_ticket))
            if positions:
                alive_mappings.append(mapping)
    finally:
        shutdown_mt5()

    return alive_mappings


def mark_execution_as_manual_close_if_needed(account: dict, execution: dict) -> bool:
    """
    Returns True if this master ticket should be treated as manually closed by client.
    """
    existing_maps = backend_get_ticket_maps_by_keys(
        license_id=execution["license_id"],
        ea_id=execution["ea_id"],
        master_ticket=execution["master_ticket"],
    )

    if not existing_maps:
        return False

    manually_closed_found = any(m.get("manually_closed") is True for m in existing_maps)
    if manually_closed_found:
        return True

    open_maps = [m for m in existing_maps if m.get("is_open") is True and m.get("client_ticket")]
    if not open_maps:
        return False

    alive_maps = get_open_mapped_tickets_for_execution(account, execution)

    # If backend thinks trades are open, but none exist in MT5 anymore,
    # then client most likely closed them manually.
    if len(open_maps) > 0 and len(alive_maps) == 0:
        backend_mark_ticket_map_closed(execution, manually_closed=True)
        print(
            f"[INFO] execution {execution['id']}: client manually closed mapped trade(s), "
            f"marking master_ticket={execution['master_ticket']} as manually_closed"
        )
        return True

    return False

def get_symbol_setting_for_execution(account: dict, execution: dict):
    requested_symbol = execution["symbol"].upper().strip()
    settings = backend_get_client_symbol_settings(account["license_key"])

    for item in settings:
        if item["symbol_name"].upper().strip() == requested_symbol:
            return item

    return None


def build_trade_comment(execution: dict) -> str:
    raw_comment = str(execution.get("comment") or "").strip()

    if raw_comment:
        return raw_comment[:30]

    return "Nolimitz Copier"

# =========================
# TRADE EXECUTION
# =========================
def execute_single_open_trade(execution: dict, account: dict) -> str:
    initialize_and_login(
        mt_login=account["mt_login"],
        mt_password=account["mt_password"],
        mt_server=account["mt_server"],
    )

    try:
        requested_symbol = execution["symbol"]
        symbol = find_broker_symbol(requested_symbol)

        symbol_setting = get_symbol_setting_for_execution(account, execution)
        if not symbol_setting:
            raise Exception(f"No client symbol setting found for {requested_symbol}")

        max_open_trades = int(symbol_setting.get("max_open_trades", 1))
        current_open_count = count_open_positions_for_symbol(symbol)

        print(
            f"Symbol setting: requested={requested_symbol}, broker={symbol}, "
            f"current_open={current_open_count}, max_open={max_open_trades}"
        )

        if current_open_count >= max_open_trades:
            raise Exception(
                f"Max open trades reached for {requested_symbol}: "
                f"{current_open_count}/{max_open_trades}"
            )

        action = str(execution["action"]).lower().strip()
        lot_size = float(execution["lot_size"] or "0.01")

        sl_raw = execution.get("sl")
        tp_raw = execution.get("tp")

        sl = float(sl_raw) if sl_raw not in [None, "", "0", 0] else 0.0
        tp = float(tp_raw) if tp_raw not in [None, "", "0", 0] else 0.0

        comment = build_trade_comment(execution)

        ensure_symbol_ready(symbol)

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise Exception(f"No tick data for symbol: {symbol}")

        order_type = mt5.ORDER_TYPE_BUY if action == "buy" else mt5.ORDER_TYPE_SELL
        price = tick.ask if action == "buy" else tick.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": WORKER_MAGIC,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        print(f"Requested symbol: {requested_symbol} -> Broker symbol: {symbol}")

        result = mt5.order_send(request)
        if result is None:
            raise Exception(f"order_send returned None: {mt5.last_error()}")

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise Exception(f"order_send failed retcode={result.retcode}")

        return str(result.order or result.deal)

    finally:
        shutdown_mt5()


def execute_open_trade(execution: dict, account: dict) -> list[str]:
    initialize_and_login(
        mt_login=account["mt_login"],
        mt_password=account["mt_password"],
        mt_server=account["mt_server"],
    )

    try:
        requested_symbol = execution["symbol"]
        symbol = find_broker_symbol(requested_symbol)

        symbol_setting = get_symbol_setting_for_execution(account, execution)
        if not symbol_setting:
            raise Exception(f"No client symbol setting found for {requested_symbol}")

        if not symbol_setting.get("enabled", True):
            raise Exception(f"Symbol is disabled for client: {requested_symbol}")

        max_open_trades = int(symbol_setting.get("max_open_trades", 1))
        trades_per_signal = int(symbol_setting.get("trades_per_signal", 1))
        current_open_count = count_open_positions_for_symbol(symbol)

        print(
            f"Symbol setting: requested={requested_symbol}, broker={symbol}, "
            f"current_open={current_open_count}, max_open={max_open_trades}, "
            f"trades_per_signal={trades_per_signal}"
        )

        available_slots = max_open_trades - current_open_count
        if available_slots <= 0:
            raise Exception(
                f"Max open trades reached for {requested_symbol}: "
                f"{current_open_count}/{max_open_trades}"
            )

        actual_trades_to_open = min(trades_per_signal, available_slots)
        tickets: list[str] = []

        shutdown_mt5()

        for _ in range(actual_trades_to_open):
            ticket = execute_single_open_trade(execution, account)
            tickets.append(str(ticket))

        return tickets

    finally:
        shutdown_mt5()


def execute_modify_trade(execution: dict, account: dict) -> list[str]:
    initialize_and_login(
        mt_login=account["mt_login"],
        mt_password=account["mt_password"],
        mt_server=account["mt_server"],
    )

    modified_tickets: list[str] = []

    try:
        mappings = backend_get_open_ticket_maps_by_keys(
            license_id=execution["license_id"],
            ea_id=execution["ea_id"],
            master_ticket=execution["master_ticket"],
        )

        if not mappings:
            raise Exception("No open ticket maps found for this master ticket")

        sl_raw = execution.get("sl")
        tp_raw = execution.get("tp")

        sl = float(sl_raw) if sl_raw not in [None, "", "0", 0] else 0.0
        tp = float(tp_raw) if tp_raw not in [None, "", "0", 0] else 0.0

        for mapping in mappings:
            client_ticket = int(mapping["client_ticket"])

            positions = mt5.positions_get(ticket=client_ticket)
            if not positions:
                print(f"[SKIP MODIFY] client trade {client_ticket} not found")
                continue

            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": client_ticket,
                "sl": sl,
                "tp": tp,
            }

            result = mt5.order_send(request)
            if result is None:
                print(f"[FAIL MODIFY] {client_ticket}: modify returned None {mt5.last_error()}")
                continue

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"[FAIL MODIFY] {client_ticket}: retcode={result.retcode}")
                continue

            modified_tickets.append(str(client_ticket))

        return modified_tickets

    finally:
        shutdown_mt5()


def execute_close_trade(execution: dict, account: dict) -> list[str]:
    initialize_and_login(
        mt_login=account["mt_login"],
        mt_password=account["mt_password"],
        mt_server=account["mt_server"],
    )

    closed_tickets: list[str] = []

    try:
        mappings = backend_get_open_ticket_maps_by_keys(
            license_id=execution["license_id"],
            ea_id=execution["ea_id"],
            master_ticket=execution["master_ticket"],
        )

        if not mappings:
            raise Exception("No open ticket maps found for this master ticket")

        for mapping in mappings:
            client_ticket = int(mapping["client_ticket"])

            positions = mt5.positions_get(ticket=client_ticket)
            if not positions:
                print(f"[SKIP CLOSE] client trade {client_ticket} already closed manually")
                continue

            position = positions[0]
            symbol = position.symbol
            volume = position.volume

            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                print(f"[FAIL CLOSE] {client_ticket}: no tick data for {symbol}")
                continue

            if position.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "position": client_ticket,
                "price": price,
                "deviation": 20,
                "magic": WORKER_MAGIC,
                "comment": execution.get("comment") or "Nolimitz Copier Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result is None:
                print(f"[FAIL CLOSE] {client_ticket}: order_send returned None {mt5.last_error()}")
                continue

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"[FAIL CLOSE] {client_ticket}: retcode={result.retcode}")
                continue

            closed_tickets.append(str(client_ticket))

       # If at least one mapped ticket was closed by worker, mark backend maps closed normally.
        if closed_tickets:
            backend_mark_ticket_map_closed(execution, manually_closed=False)
        else:
            # If nothing was closable and client already removed them manually,
            # mark as manually closed so they never reopen.
            alive_maps = get_open_mapped_tickets_for_execution(account, execution)
            if not alive_maps:
                backend_mark_ticket_map_closed(execution, manually_closed=True)
                print(
                    f"[INFO] close execution {execution['id']}: "
                    f"all mapped tickets already missing, marked manually_closed=True"
                )

        return closed_tickets

    finally:
        shutdown_mt5()


# =========================
# CORE PROCESSOR
# =========================
def process_execution(execution: dict):
    execution_id = execution["id"]

    try:
        account = backend_get_execution_account(execution_id)

        if execution["event_type"] == "open":
            if is_stale_open_execution(execution):
                backend_update_execution(
                    execution_id=execution_id,
                    status="skipped",
                    client_ticket=None,
                    error_message="Skipped old open event",
                )
                print(f"[SKIP] execution {execution_id}: old open event")
                return

            # Bulletproof manual-close protection
            if mark_execution_as_manual_close_if_needed(account, execution):
                backend_update_execution(
                    execution_id=execution_id,
                    status="skipped",
                    client_ticket=None,
                    error_message="Trade was manually closed by client; will not reopen",
                )
                print(f"[SKIP] execution {execution_id}: manually closed trade will not reopen")
                return

            existing_maps = backend_get_ticket_maps_by_keys(
                license_id=execution["license_id"],
                ea_id=execution["ea_id"],
                master_ticket=execution["master_ticket"],
            )

            if existing_maps:
                open_map_found = False

                for existing_map in existing_maps:
                    mapped_client_ticket = existing_map.get("client_ticket")
                    if existing_map.get("is_open") is True and mapped_client_ticket:
                        if mapped_ticket_still_open(account, mapped_client_ticket):
                            open_map_found = True
                            break

                if open_map_found:
                    backend_update_execution(
                        execution_id=execution_id,
                        status="skipped",
                        client_ticket=None,
                        error_message="Trade already exists for this master ticket",
                    )
                    print(f"[SKIP] execution {execution_id}: duplicate open prevented")
                    return

                # If maps exist but no live trade exists and they were not manually closed,
                # then they are stale maps from an old failed/open state.
                try:
                    backend_mark_ticket_map_closed(execution, manually_closed=False)
                    print(
                        f"[INFO] execution {execution_id}: stale open maps detected, "
                        f"maps closed and continuing"
                    )
                except Exception as e:
                    print(f"[WARN] execution {execution_id}: could not close stale maps: {e}")

            tickets = execute_open_trade(execution, account)
            first_ticket = tickets[0] if tickets else None

            for idx, ticket in enumerate(tickets, start=1):
                backend_upsert_ticket_map(
                    execution=execution,
                    client_ticket=ticket,
                    is_open=True,
                    manually_closed=False,
                    child_ticket_index=idx,
                )

            backend_update_execution(
                execution_id=execution_id,
                status="executed" if tickets else "skipped",
                client_ticket=first_ticket,
                error_message=None if tickets else "No child trades were opened",
            )
            print(f"[OK] execution {execution_id} opened {len(tickets)} trade(s): {tickets}")
            return

        if execution["event_type"] == "modify":
            modified_tickets = execute_modify_trade(execution, account)
            backend_update_execution(
                execution_id=execution_id,
                status="executed" if modified_tickets else "skipped",
                client_ticket=",".join(modified_tickets) if modified_tickets else None,
                error_message=None if modified_tickets else "No child trades were modified",
            )
            print(f"[OK] execution {execution_id} modified tickets: {modified_tickets}")
            return

        if execution["event_type"] == "close":
            closed_tickets = execute_close_trade(execution, account)
            backend_update_execution(
                execution_id=execution_id,
                status="executed" if closed_tickets else "skipped",
                client_ticket=",".join(closed_tickets) if closed_tickets else None,
                error_message=None if closed_tickets else "No child trades were closed",
            )
            print(f"[OK] execution {execution_id} closed tickets: {closed_tickets}")
            return

        backend_update_execution(
            execution_id=execution_id,
            status="failed",
            client_ticket=None,
            error_message=f"Unknown event type: {execution['event_type']}",
        )

    except Exception as e:
        message = str(e)

        status = "failed"
        if "Max open trades reached" in message:
            status = "skipped"
        if "Skipped old open event" in message:
            status = "skipped"
        if "No client symbol setting found" in message:
            status = "skipped"
        if "Trade already exists for this master ticket" in message:
            status = "skipped"
        if "Trade was manually closed by client; will not reopen" in message:
            status = "skipped"
        if "Symbol is disabled for client" in message:
            status = "skipped"

        backend_update_execution(
            execution_id=execution_id,
            status=status,
            client_ticket=None,
            error_message=message,
        )

        label = "SKIP" if status == "skipped" else "FAIL"
        print(f"[{label}] execution {execution_id}: {message}")


# =========================
# LOOP
# =========================
def main():
    print("Nolimitz MT5 Execution Worker started...")
    while True:
        try:
            executions = backend_claim_pending_executions()
            if executions:
                print(f"Found {len(executions)} pending executions")
                for execution in executions:
                    process_execution(execution)
            time.sleep(POLL_SECONDS)
        except Exception as e:
            print(f"[WORKER ERROR] {e}")
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()