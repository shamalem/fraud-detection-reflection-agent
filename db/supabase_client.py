"""Supabase-backed transaction tools: the agent's only window into the transaction data."""
from functools import lru_cache

from supabase import Client, create_client

from config import settings


@lru_cache(maxsize=1)
def get_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_key)


def get_transaction(transaction_id: str) -> dict | None:
    """Retrieve one transaction by Transaction_ID."""
    response = (
        get_client()
        .table(settings.supabase_table)
        .select("*")
        .eq("Transaction_ID", transaction_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def get_user_transactions(user_id: str, limit: int = 20) -> list[dict]:
    response = (
        get_client()
        .table(settings.supabase_table)
        .select("*")
        .eq("User_ID", user_id)
        .order("Timestamp", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data


def get_recent_user_transactions(user_id: str, before_timestamp: str, limit: int = 10) -> list[dict]:
    """Recent transactions for a user that occurred before the target transaction's timestamp."""
    response = (
        get_client()
        .table(settings.supabase_table)
        .select("*")
        .eq("User_ID", user_id)
        .lt("Timestamp", before_timestamp)
        .order("Timestamp", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data


def get_user_summary(user_id: str, before_timestamp: str) -> dict | None:
    """Compact summary of a user's historical behavior before the target transaction's timestamp."""
    response = (
        get_client()
        .table(settings.supabase_table)
        .select(
            "Transaction_Amount,Transaction_Type,Location,"
            "Device_Type,IP_Address_Flag,Previous_Fraudulent_Activity,"
            "Failed_Transaction_Count_7d,Authentication_Method"
        )
        .eq("User_ID", user_id)
        .lt("Timestamp", before_timestamp)
        .execute()
    )

    rows = response.data
    if not rows:
        return None

    amounts = [r["Transaction_Amount"] for r in rows]

    return {
        "transaction_count": len(rows),
        "average_transaction_amount": sum(amounts) / len(amounts),
        "max_transaction_amount": max(amounts),
        "locations": list(set(r["Location"] for r in rows)),
        "transaction_types": list(set(r["Transaction_Type"] for r in rows)),
        "devices": list(set(r["Device_Type"] for r in rows)),
        "authentication_methods": list(set(r["Authentication_Method"] for r in rows)),
        "transactions_with_ip_flag": sum(r["IP_Address_Flag"] == 1 for r in rows),
        "transactions_with_previous_fraud": sum(r["Previous_Fraudulent_Activity"] == 1 for r in rows),
    }
