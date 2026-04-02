from pydantic import BaseModel


class CreateClientRequest(BaseModel):
    client_id: str
    name: str


class UpdateClientRequest(BaseModel):
    name: str


class ClientResponse(BaseModel):
    id: int
    client_id: str
    name: str
    status: str
