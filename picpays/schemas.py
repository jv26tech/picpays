from pydantic import BaseModel

from picpays.models import UserRole


class UserSchema(BaseModel):
    name: str
    document: str
    email: str
    amount: float
    role: UserRole


class CreateUserSchema(UserSchema):
    password: str


class CreateTransferSchema(BaseModel):
    value: float
    payer: int
    payee: int
