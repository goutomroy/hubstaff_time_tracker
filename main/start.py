import argparse
import asyncio
import json
import logging
import os
from pathlib import Path
from datetime import date, timedelta, datetime
import requests
from runtime_calculator import timer
from utils import get_auth_url
from utils import REQUEST_TIMEOUT
from utils import get_user_organization_url


def install_required_pakgs():
    file_path = Path(__file__).resolve().parent.parent.joinpath('requirements.txt')
    with open(file_path) as my_file:
        desired_pkgs = " ".join([each.strip().split("==")[0] for each in my_file.readlines()])
        my_cmd = "python3.7 -m pip install " + desired_pkgs
        os.system(my_cmd)


def get_auth_token(request_obj, app_token, email, password):
    post_data = {'email': email, 'password': password}
    headers = {'App-Token': app_token}
    response = request_obj.post(get_auth_url(), data=post_data, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    return data['user']['auth_token'], data['user']['id']


def get_user_organizations(request_obj, app_token, auth_token, user_id):
    headers = {'App-Token': app_token, 'Auth-Token': auth_token}
    response = request_obj.get(get_user_organization_url(user_id),  headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    if not data['organizations']:
        raise Exception("No organization found for user.")
    return data['organizations'][0]


@timer
def main():
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument('-app_token', '--app_token', dest="app_token", type=str, required=True, help="App token is required")
    my_parser.add_argument('-date', '--date', dest="date", default=date.today() - timedelta(days=1),
                           type=lambda d: datetime.strptime(d, '%Y-%m-%d').date(), help="Date in the format yyyy-mm-dd",
                           required=False)
    my_parser.add_argument('-email', '--email', dest="email", type=str, required=True, help="Email is required")
    my_parser.add_argument('-password', '--password', dest="password", type=str, required=True,
                           help="Password is required")
    cmd_args = my_parser.parse_args()

    try:
        install_required_pakgs()

        with requests.Session() as request_obj:
            auth_token, user_id = get_auth_token(request_obj, cmd_args.app_token, cmd_args.email, cmd_args.password)
            organization = get_user_organizations(request_obj, cmd_args.app_token, auth_token, user_id)

        from ReefTimeTracker import TimeTracker
        time_tracker = TimeTracker(cmd_args.app_token, cmd_args.date, organization)
        asyncio.run(time_tracker.pull_data(auth_token))

    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    main()
