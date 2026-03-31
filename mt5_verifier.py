from fastapi import FastAPI
from pydantic import BaseModel, model_validator
import MetaTrader5 as mt5

app = FastAPI(title="Nolimitz MT5 Verifier")


class MT5VerifyRequest(BaseModel):
    login: str
    password: str
    server: str

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, data):
        if not isinstance(data, dict):
            return data

        return {
            "login": str(data.get("login") or data.get("mt_login") or "").strip(),
            "password": str(data.get("password") or data.get("mt_password") or "").strip(),
            "server": str(data.get("server") or data.get("mt_server") or "").strip(),
        }


@app.get("/")
def root():
    return {"message": "MT5 verifier is running"}


@app.post("/verify-mt5")
def verify_mt5(data: MT5VerifyRequest):
    if not data.login or not data.password or not data.server:
        return {
            "success": False,
            "message": "Missing MT5 login, password, or server"
        }

    try:
        login = int(data.login)
    except ValueError:
        return {
            "success": False,
            "message": "MT5 login must be numeric"
        }

    initialized = mt5.initialize()
    if not initialized:
        return {
            "success": False,
            "message": f"MT5 initialize failed: {mt5.last_error()}"
        }

    try:
        authorized = mt5.login(login, password=data.password, server=data.server)

        if not authorized:
            return {
                "success": False,
                "message": f"MT5 login failed: {mt5.last_error()}"
            }

        account = mt5.account_info()
        if account is None:
            return {
                "success": False,
                "message": "MT5 login succeeded but account info is unavailable"
            }

        return {
            "success": True,
            "message": "MT5 verified successfully",
            "login": account.login,
            "name": account.name,
            "server": account.server,
            "balance": account.balance,
        }

    finally:
        mt5.shutdown()