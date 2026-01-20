from datetime import datetime
from db import users_collection

def upsert_google_user(user: dict):
    users_collection.update_one(
        {"email": user["email"]},
        {
            "$set": {
                "name": user["name"],
                "picture": user.get("picture"),
                "last_login": datetime.utcnow()
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow(),
                "profile": {}
            }
        },
        upsert=True
    )

def get_user_by_email(email: str):
    return users_collection.find_one(
        {"email": email},
        {"_id": 0}
    )
