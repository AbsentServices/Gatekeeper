import sys
import os
from pathlib import Path

# Add parent directory to path so we can import `database.py`
sys.path.append(str(Path(__file__).resolve().parent.parent))
import database

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Gatekeeper Security Web Panel", version="1.0.0")

class BlacklistAddRequest(BaseModel):
    user_id: int
    reason: str
    admin_id: int = 0

@app.get("/api/blacklist")
def get_blacklist():
    """API endpoint to retrieve all blacklisted users with details."""
    try:
        entries = database.get_all_blacklisted_users()
        # Enrich entries with formatted metadata if needed
        return {"success": True, "count": len(entries), "data": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/blacklist/{user_id}")
def remove_blacklist(user_id: int):
    """API endpoint to remove a user from the global blacklist."""
    success = database.remove_from_global_blacklist(user_id)
    if success:
        return {"success": True, "message": f"User {user_id} removed from blacklist."}
    raise HTTPException(status_code=404, detail="User not found on blacklist.")

@app.post("/api/blacklist")
def add_blacklist(payload: BlacklistAddRequest):
    """API endpoint to add a user to the global blacklist."""
    success = database.add_to_global_blacklist(payload.user_id, payload.reason, payload.admin_id)
    if success:
        return {"success": True, "message": f"User {payload.user_id} blacklisted successfully."}
    raise HTTPException(status_code=400, detail="Failed to add user to blacklist.")

# Serve static frontend files from the webpannel directory
app.mount("/", StaticFiles(directory=os.path.dirname(__file__), html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)