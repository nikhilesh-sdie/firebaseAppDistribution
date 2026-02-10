import os
import re
import json
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ---------------- CONFIG ----------------
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

# project_number = os.getenv("project_number")
# app_id = os.getenv("app_id")
# apkEnv = os.getenv("app_env", "QA")
# version_display = os.getenv("displayVersion")
# version_build = os.getenv("buildVersion")
# # print(version_build)
# # raw = os.getenv("sa_key")
# # print("raw type:", type(raw))
# # if not raw:
# #     raise RuntimeError("❌ sa_key is missing")

# #sa_info = os.getenv("sa_key")
# raw = os.getenv("sa_key")
# sa_info = json.loads(raw)
# print("sa type:", type(sa_info))

#validation


def must(name):
    val = os.getenv(name)
    print(f"{name}: {'SET' if val else 'MISSING'}")
    return val

project_number = must("project_number")
app_id = must("app_id")
apkEnv = os.getenv("app_env", "QA")
version_display = os.getenv("displayVersion")
version_build = os.getenv("buildVersion")

raw = must("sa_key")

# Hard stop if any required value is missing
missing = [k for k,v in {
    "project_number": project_number,
    "app_id": app_id,
    "sa_key": raw
}.items() if not v]

if missing:
    raise RuntimeError(f"❌ Missing env vars: {missing}")

# Parse SA JSON
try:
    sa_info = json.loads(raw)
    print("sa_key parsed OK")
except Exception as e:
    print("❌ sa_key JSON invalid:", e)
    sys.exit(1)

print("sa_info type:", type(sa_info))


# ---------------- AUTH ----------------
def auth(sa_info):
    creds = service_account.Credentials.from_service_account_info(
        sa_info, scopes=SCOPES
    )
    service = build("firebaseappdistribution", "v1", credentials=creds)

    parent = f"projects/{project_number}/apps/{app_id}"
    releases = service.projects().apps().releases().list(parent=parent).execute()

    if "releases" not in releases:
        raise Exception("❌ No releases found")

    return service, creds, releases["releases"]

# ---------------- FETCH BY VERSION ----------------
def fetch_apk_by_version(releases):
    version_name = None
    apk_name = None
    iteration = 0
    matching_versions = []
    for increamentor in releases:
        if version_display == increamentor.get("displayVersion", ""):
            matching_versions.append(increamentor)
        else:
            print("Searching for the matching version...")

    if not matching_versions:
        print(f"⚠️ Version {version_display} not found, falling back to env based search...")
        return fetch_latest_apk_by_env(releases)

    build_list = [r.get("buildVersion") for r in matching_versions]

    for r in matching_versions:
        
        if version_build == r.get("buildVersion"):
            display = r.get("displayVersion", "")
            build = r.get("buildVersion", "")
            version_name = r["name"]
            apk_name = f"{display}({build})"
            note = r.get("releaseNotes", {}).get("text", "")
            print("Found matching build:", apk_name)
            print("-----")
            print("📦 Release:", r["name"])
            print("Version:", r.get("displayVersion"))
            print("Build:", r.get("buildVersion"))
            print("Notes:", note)
            return version_name, apk_name

    if not version_name:
        print(f"Apk {version_display}({version_build}) not found.")
        print(f"Fetching latest available build for {version_display}")
        version_name = matching_versions[0]["name"]
        apk_name = f"{matching_versions[0].get('displayVersion')}({matching_versions[0].get('buildVersion')})"
        note = matching_versions[0].get("releaseNotes", {}).get("text", "")
        print("Found:", apk_name)
        print("-----")
        print("📦 Release:", matching_versions[0]["name"])
        print("Version:", matching_versions[0].get("displayVersion"))
        print("Build:", matching_versions[0].get("buildVersion"))
        print("Notes:", note)
        print("-----")
        

    return version_name, apk_name

# ---------------- FETCH BY ENV ----------------
def fetch_latest_apk_by_env(releases):
    key = apkEnv.lower()
    print(f"Fetching latest {key} apk")
    version_name = None
    apk_name = None

    for increamentor in range(len(releases)):
        r = releases[increamentor]
        note = r.get("releaseNotes", {}).get("text", "")
        items = [x.lower() for x in re.split(r"[|,\s]+", note.strip()) if x]
        if key in items:
            print("-----")
            print("📦 Latest release:", r["name"])
            print("Version:", r.get("displayVersion"))
            print("Build:", r.get("buildVersion"))
            print("Created:", r.get("createTime"))
            print("Notes:", note)

            version_name = r["name"]
            apk_name = f"{r.get('displayVersion')}({r.get('buildVersion')})"
            break
        else:
            print(f"⚠️ {key} apk not found, fetching latest apk...")
            fetch_latest_apk(releases)

    return version_name, apk_name

# ---------------- FETCH LATEST ----------------
def fetch_latest_apk(releases):
    print(f"Fetching Latest apk")
    r = releases[0]
    note = r.get("releaseNotes", {}).get("text", "")
    key = apkEnv.lower()

    items = [x.lower() for x in re.split(r"[|,\s]+", note.strip()) if x]

    if key in items:
        print("-----")
        print("📦 Latest release:", r["name"])
        print("Version:", r.get("displayVersion"))
        print("Build:", r.get("buildVersion"))
        print("Created:", r.get("createTime"))
        print("Notes:", note)
        version_name = r["name"]
        apk_name = f"{r.get('displayVersion')}({r.get('buildVersion')})"
        return version_name, apk_name

    raise Exception("❌ No latest release found")

# ---------------- DOWNLOAD ----------------
def download_apk(service, creds, version_name, apk_name):
    resp = service.projects().apps().releases().get(
        name=version_name
    ).execute()

    url = resp["binaryDownloadUri"]

    print("⬇️ Downloading APK...")
    r = requests.get(url, headers={"Authorization": f"Bearer {creds.token}"}, stream=True)

    with open(apk_name, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)

    print(f"✅ Saved as {apk_name}")

    github_env = os.getenv("GITHUB_ENV")
    if github_env:
        with open(github_env, "a") as f:
            f.write(f"APK_PATH={apk_name}\n")

# ---------------- MAIN ----------------
print("Authenticating with firebase...")
service, creds, releases = auth(sa_info)
print("Checking and validating configs")
if version_display and version_build:
    version_name, apk_name = fetch_apk_by_version(releases)
elif apkEnv:
    version_name, apk_name = fetch_latest_apk_by_env(releases)
else:
    version_name, apk_name = fetch_latest_apk(releases)

download_apk(service, creds, version_name, apk_name)