from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from redis import Redis
from rq import Queue, Retry
from sqlalchemy.orm import Session

from picpays.database import get_session
from picpays.jobs import send_notification
from picpays.schemas import CreateTransferSchema, CreateUserSchema
from picpays.services import (
    add_user,
    check_user_balance,
    check_user_role,
    get_user_by_id,
    make_transfer,
)

app = FastAPI()
redis_conn = Redis(host='localhost', port=6379)
task_queue = Queue('task_queue', connection=redis_conn)


@app.get('/')
def index():
    return {'hello': 'world'}


@app.post('/user/', status_code=HTTPStatus.CREATED)
def create_user(
    user: CreateUserSchema, session: Session = Depends(get_session)
):
    db_user = add_user(user, session)

    return db_user


@app.post('/transfer/', status_code=HTTPStatus.CREATED)
def transfer(
    transfer_data: CreateTransferSchema,
    session: Session = Depends(get_session),
):
    payer = get_user_by_id(transfer_data.payer, session)

    # Check balance
    check_user_balance(payer, transfer_data.value)

    # Check role
    check_user_role(payer)

    payee = get_user_by_id(transfer_data.payee, session)

    transfer_db = make_transfer(payer, payee, transfer_data, session)
    if not transfer_db:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Transfer not authorized'
        )

    task_queue.enqueue(send_notification, retry=Retry(max=5, interval=10))
    return transfer_db
