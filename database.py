# --- Fetch All Blacklisted Users ---
def get_all_blacklisted_users() -> list[dict]:
    """Fetch all globally blacklisted users ordered by newest first."""
    response = (
        supabase.table("global_blacklist")
        .select("user_id, reason, added_at")
        .order("added_at", desc=True)
        .execute()
    )
    return response.data if response.data else []