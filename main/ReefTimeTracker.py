import asyncio
import logging
import time
import webbrowser
from datetime import timedelta, datetime, date
import aiohttp
from itertools import groupby
from operator import itemgetter
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from utils import REQUEST_TIMEOUT, get_user_organization_url, get_organization_projects_url, \
    get_organization_members_url, get_organization_activities_url, get_auth_url


logging.basicConfig(level=logging.INFO)


class TimeTracker:

    def __init__(self, app_token: str, requested_date: date, organization: dict):
        self.app_token = app_token
        self.requested_date = requested_date
        self.organization = organization

    async def get_organization_activities(self, session):
        start_time = datetime.combine(self.requested_date, datetime.min.time())
        stop_time = start_time + timedelta(hours=23, minutes=59)
        params = {'organizations': self.organization['id'], 'start_time': start_time.isoformat() + "Z",
                  'stop_time': stop_time.isoformat() + "Z"}
        async with session.get(get_organization_activities_url(), params=params) as response:
            data = await response.json()

        if not data['activities']:
            raise Exception("No activities found for organization on that given day.")
        return data['activities']

    async def get_organization_members(self, session):
        async with session.get(get_organization_members_url(self.organization['id'])) as response:
            data = await response.json()

        if not data['users']:
            raise Exception("No members found for organization.")
        return data['users']

    async def get_organization_projects(self, session):
        async with session.get(get_organization_projects_url(self.organization['id'])) as response:
            data = await response.json()

        if not data['projects']:
            raise Exception("No projects found for organization.")
        return data['projects']

    def render_webpage(self, rows_header, rows_data):
        template_dir = Path(__file__).resolve().parent.parent.joinpath('templates')
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("render_data.html")
        output = template.render(organization_name=self.organization['name'], rows_header=rows_header, rows_data=rows_data,
                                 requested_date=self.requested_date)
        file_path = template_dir.joinpath('hub_time_tracker.html')
        with open(file_path, 'w') as my_file:
            my_file.write(output)
        webbrowser.open_new_tab('file:///'+str(file_path))

    def populate_required_data(self, organization_projects, organization_members, organization_activities):
        unique_user_ids, unique_project_ids = [], []
        for each in organization_activities:
            if each['user_id'] not in unique_user_ids:
                unique_user_ids.append(each['user_id'])
            if each['project_id'] not in unique_project_ids:
                unique_project_ids.append(each['project_id'])

        grouper = itemgetter("project_id", "user_id")
        worked_time_data = []
        for key, grp in groupby(sorted(organization_activities, key=grouper), grouper):
            temp_dict = {"project_id": key[0], "user_id": key[1],
                         "tracked": time.strftime("%H:%M", time.gmtime(sum(item["tracked"] for item in grp)))}
            worked_time_data.append(temp_dict)

        rows_header_data = [""]
        for uid in unique_user_ids:
            for each in organization_members:
                if uid == each['id']:
                    rows_header_data.append(each['name'])
                    break

        rows_time_data = []
        for pid in unique_project_ids:
            each_row = []
            for org in organization_projects:
                if org['id'] == pid:
                    each_row.append(org['name'])
                    break
            for uid in unique_user_ids:
                for wtd in worked_time_data:
                    if wtd['user_id'] == uid and wtd['project_id'] == pid:
                        each_row.append(wtd['tracked'])
                        break
                else:
                    each_row.append("")
            rows_time_data.append(each_row)

        return rows_header_data, rows_time_data

    async def pull_data(self, auth_token: str):
        headers = {'App-Token': self.app_token, 'Auth-Token': auth_token}
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=150), raise_for_status=True,
                                         headers=headers) as session:

            tasks = [asyncio.create_task(self.get_organization_projects(session)),
                     asyncio.create_task(self.get_organization_members(session)),
                     asyncio.create_task(self.get_organization_activities(session))]
            try:
                results = await asyncio.gather(*tasks, return_exceptions=False)
                rows_header_data, rows_time_data = self.populate_required_data(*[each for each in results])
                self.render_webpage(rows_header_data, rows_time_data)
            except Exception as e:
                for each in tasks:
                    if not each.done():
                        each.cancel()
                raise e
