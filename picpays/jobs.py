from http import HTTPStatus

import requests


def send_notification():
    res = requests.post('https://util.devi.tools/api/v1/notify')
    print(res)

    if res.status_code != HTTPStatus.NO_CONTENT:
        raise Exception('Could not send notification')

    return res
