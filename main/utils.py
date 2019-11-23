

REQUEST_TIMEOUT = 50
BASE_URL = "https://api.hubstaff.com/v1/"


def get_auth_url():
    return f"{BASE_URL}auth"


def get_organization_activities_url():
    url = "https://api.hubstaff.com/v1/activities"
    return url


def get_organization_projects_url(organization_id):
    url = f"{BASE_URL}organizations/{organization_id}/projects"
    return url


def get_organization_members_url(organization_id):
    url = f"{BASE_URL}organizations/{organization_id}/members?include_removed=false"
    return url


def get_user_organization_url(user_id):
    url = f"{BASE_URL}users/{user_id}/organizations"
    return url


def get_project_members_url(project_id):
    url = f"{BASE_URL}projects/{project_id}/members?include_removed=false"
    return url



