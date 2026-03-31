import time
import requests

BACKEND = "http://127.0.0.1:8000"
WORKER_NAME = "nolimitz-worker-1"


def get_pending_jobs():
    try:
        res = requests.get(f"{BACKEND}/worker/jobs/pending", timeout=15)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("Failed to fetch jobs:", e)
        return []


def claim_job(job_id: int):
    try:
        res = requests.post(
            f"{BACKEND}/worker/jobs/{job_id}/claim",
            params={"worker_name": WORKER_NAME},
            timeout=15,
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Failed to claim job {job_id}:", e)
        return None


def complete_job(job_id: int, status: str, error_message: str | None = None):
    try:
        payload = {
            "status": status,
            "worker_name": WORKER_NAME,
            "error_message": error_message,
            "processed_at": None,
        }
        res = requests.post(
            f"{BACKEND}/worker/jobs/{job_id}/complete",
            json=payload,
            timeout=15,
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Failed to complete job {job_id}:", e)
        return None


def execute_mt5_trade(job: dict):
    try:
        res = requests.post(
            "http://127.0.0.1:8011/execute-trade",
            json={
                "mt_login": job["mt_login"],
                "mt_password": job["mt_password"],
                "mt_server": job["mt_server"],
                "symbol": job["symbol"],
                "action": job["action"],
                "lot": job["volume"],
                "sl": job["stop_loss"],
                "tp": job["take_profit"],
            },
            timeout=30,
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def loop():
    print("Nolimitz multi bridge started...")

    while True:
        jobs = get_pending_jobs()

        if not jobs:
            time.sleep(3)
            continue

        for job in jobs:
            claimed = claim_job(job["id"])
            if not claimed:
                continue

            result = execute_mt5_trade(job)

            if result.get("success"):
                complete_job(job["id"], "success")
                print(f"Job {job['id']} executed successfully")
            else:
                complete_job(job["id"], "failed", result.get("error") or result.get("message"))
                print(f"Job {job['id']} failed:", result)

        time.sleep(2)


if __name__ == "__main__":
    loop()