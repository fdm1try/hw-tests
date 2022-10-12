from time import sleep
import requests
import os
import pytest
from datetime import date, datetime

DIR_NAME = date.today().strftime('TEST_%d-%m-%Y')
TOKEN = os.environ.get('YADISK_TOKEN') or 'paste yandex disk REST API token'


def wait_async_op(url, timeout=10):
    start = datetime.now()
    while True:
        response = requests.get(url, headers={'Authorization': f'OAuth {TOKEN}'})
        status = response.json().get('status')
        if status == 'success':
            return True
        if status != 'in-progress':
            return False
        sleep(0.5)
        if (datetime.now() - start).seconds >= timeout:
            return False


def api_call(method, url, params: dict = None):
    def decorator(old_function):
        def new_function():
            response = requests.request(method=method, url=url, params=params, headers={
                'Authorization': f'OAuth {TOKEN}'
            })
            return old_function(response)
        return new_function
    return decorator


@api_call('get', 'https://cloud-api.yandex.net/v1/disk')
def setup(response: requests.Response):
    if response.status_code != 200:
        error = response.json()
        pytest.exit(f'It is not possible to check the API functions, HTTP response code {response.status_code}: '
                    f'{error.get("message")} [{error.get("error")}]')


@api_call('get', 'https://cloud-api.yandex.net/v1/disk/resources', {'path': DIR_NAME})
def test_dir_not_exist(response: requests.Response):
    assert response.status_code == 404


@api_call('put', 'https://cloud-api.yandex.net/v1/disk/resources', {'path': DIR_NAME})
def test_dir_create(response: requests.Response):
    assert response.status_code == 201


@api_call('get', 'https://cloud-api.yandex.net/v1/disk/resources', {'path': DIR_NAME})
def test_dir_exist(response: requests.Response):
    assert response.status_code == 200


@api_call('put', 'https://cloud-api.yandex.net/v1/disk/resources', {'path': DIR_NAME})
def test_error_create_duplicate_dir(response: requests.Response):
    assert response.status_code == 409


@api_call('put', 'https://cloud-api.yandex.net/v1/disk/resources', {'path': f'{DIR_NAME}/{DIR_NAME}'})
def test_dir_create_child(response: requests.Response):
    assert response.status_code == 201


@api_call('delete', 'https://cloud-api.yandex.net/v1/disk/resources', {'path': DIR_NAME, 'permanent': True})
def test_dir_delete(response: requests.Response):
    assert response.status_code in [202, 204]
    if response.status_code == 202:
        assert wait_async_op(response.json().get('href')) is True


@api_call('delete', 'https://cloud-api.yandex.net/v1/disk/resources', {'path': DIR_NAME})
def test_error_delete(response: requests.Response):
    assert response.status_code == 404
