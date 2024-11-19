from http import HTTPStatus

import requests
from fastapi import HTTPException

from picpays.models import Transfer


def authorize_transfer():
    res = requests.get('https://util.devi.tools/api/v2/authorize').json()
    auth = res['data']['authorization']
    print(auth)
    if not auth:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Transfer not authorized'
        )


def make_transfer(payer, payee, transfer_data, session):
    transfer_db = Transfer(
        amount=transfer_data.value,
        payer_id=transfer_data.payer,
        payee_id=transfer_data.payee,
    )
    try:
        payer.pay(amount=transfer_data.value)
        payee.receive(amount=transfer_data.value)

        session.add(transfer_db)
        authorize_transfer()
        session.commit()
        session.refresh(transfer_db)
    except Exception:
        session.rollback()
