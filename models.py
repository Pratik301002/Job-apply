from pydantic import BaseModel
from typing import Optional, List

class GoogleUser(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None

class FillRequest(BaseModel):
    user: GoogleUser
    fields: List[dict]
