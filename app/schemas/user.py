from typing import Optional, Union

from pydantic import BaseModel, EmailStr


class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str] = None
    client_id: Union[str, int, None] = None
