from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from picpays.database import get_session
from picpays.models import User, UserRole
from picpays.schemas import CreateUserSchema, TransferSchema
from picpays.services import make_transfer

app = FastAPI()


@app.get('/')
def index():
    return {'hello': 'world'}


@app.post('/users/', status_code=HTTPStatus.CREATED)
def create_user(
    user: CreateUserSchema, session: Session = Depends(get_session)
):
    db_user = session.scalar(
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


@app.post('/transfer/')
def transfer(
    transfer_data: TransferSchema, session: Session = Depends(get_session)
):
    payer = session.scalar(
        select(User).where((User.id == transfer_data.payer))
    )

    if not payer:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail='Payer does not exist'
        )

    # Check balance
    if payer.amount < transfer_data.value:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough balance'
        )

    # Check role
    if payer.role == UserRole.SELLER:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='Payer does not have enough permissions',
        )

    payee = session.scalar(
        select(User).where((User.id == transfer_data.payee))
    )
    if not payee:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail='Payee does not exist'
        )

    transfer_db = make_transfer(payer, payee, transfer_data, session)
    if not transfer_db:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Transfer not authorized'
        )
    return transfer_db
