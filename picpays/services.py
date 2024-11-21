from http import HTTPStatus

import requests
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from picpays.database import transactional
from picpays.models import Transfer, User, UserRole
from picpays.schemas import CreateTransferSchema, CreateUserSchema


def get_user_by_mail_or_document(
    user: CreateUserSchema, session: Session
) -> None:
    db_user: User | None = session.scalar(
        select(User).where(
            (User.document == user.document) | (User.email == user.email)
        )
    )

    if db_user:
        if db_user.document == user.document:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Document already registered',
            )
        elif db_user.email == user.email:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Email already registered',
            )


def add_user(user: CreateUserSchema, session: Session) -> User:
    get_user_by_mail_or_document(user, session)

    db_user = User(
        name=user.name,
        email=user.email,
        password=user.password,
        document=user.document,
        role=user.role,
        amount=user.amount,
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


def get_user_by_id(id: int, session: Session) -> User:
    user = session.scalar(select(User).where((User.id == id)))
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail='Payer does not exist'
        )
    return user


def check_user_balance(payer: User, value: float) -> None:
    if payer.amount < value:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough balance'
        )


def check_user_role(user: User) -> None:
    if user.role == UserRole.SELLER:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='Payer does not have enough permissions',
        )


def authorize_transfer() -> None:
    res = requests.get('https://util.devi.tools/api/v2/authorize').json()
    auth = res['data']['authorization']
    print(auth)
    if not auth:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Transfer not authorized'
        )


@transactional
def make_transfer(
    payer: User,
    payee: User,
    transfer_data: CreateTransferSchema,
    session: Session,
) -> Transfer:
    transfer_db = Transfer(
        amount=transfer_data.value,
        payer_id=transfer_data.payer,
        payee_id=transfer_data.payee,
    )
    payer.pay(amount=transfer_data.value)
    payee.receive(amount=transfer_data.value)

    session.add(transfer_db)
    authorize_transfer()
    return transfer_db
