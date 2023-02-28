from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    role: int
    disabled: bool

class UserDB(User):
    password: str

class UsersList(BaseModel):
    list: list[User]

