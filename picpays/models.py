import enum

from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship

table_registry = registry()
Base = declarative_base()


class UserRole(enum.Enum):
    SELLER = 'seller'
    CUSTOMER = 'customer'


class User(Base):  # type:ignore
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    document: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    amount: Mapped[float]
    role: Mapped[UserRole]

    def pay(self, amount):
        self.amount -= amount

    def receive(self, amount):
        self.amount += amount


class Transfer(Base):  # type:ignore
    __tablename__ = 'transfer'

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[float]
    payer_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    payee_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    payer: Mapped['User'] = relationship(foreign_keys=[payer_id])
    payee: Mapped['User'] = relationship(foreign_keys=[payee_id])
