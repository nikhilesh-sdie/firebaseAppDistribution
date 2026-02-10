# 🚀 firebaseAppDistribution
### GitHub Action to fetch APKs from Firebase App Distribution

A lightweight GitHub Action written in **Python** that allows you to **fetch and download Android APKs directly from Firebase App Distribution** during your CI/CD workflows.

Use this action to automatically pull the correct app build for testing, automation, or deployment pipelines.

---

## ✨ Features

- 📦 Download APKs from Firebase App Distribution
- 🔍 Fetch by:
  - exact `displayVersion + buildVersion`
  - latest build for a version
  - latest release by environment tag
- 🔁 Automatic fallback logic
- 🔐 Secure authentication using Firebase Service Account
- ⚡ Works in GitHub Actions and locally

---

## 🔧 Prerequisites

- A Firebase project
- Firebase App Distribution enabled
- A **Service Account JSON key** with:
  - *Firebase App Distribution Viewer* or higher
- Your:
  - **Project Number**
  - **Firebase App ID**

---

## 📦 Usage

### Example GitHub Workflow

```yaml
name: Fetch APK from Firebase

on:
  workflow_dispatch:

jobs:
  fetch-android-apk:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Fetch Android APK
        uses: nikhilesh-sdie/firebaseAppDistribution@main
        with:
          project_id: ${{ secrets.FIREBASE_PROJECT_ID }}
          app_id: ${{ secrets.FIREBASE_APP_ID }}
          app_env: QA
          displayVersion: "1.0.2"
          buildVersion: "93"
          sa_key: ${{ secrets.FIREBASE_SA_KEY }}

```

### Inputs

| Input            | Description                                           | Required | Default |
| ---------------- | ----------------------------------------------------- | -------- | ------- |
| `project_id`     | Firebase project number                               | Yes      | –       |
| `app_id`         | Firebase App ID                                       | Yes      | –       |
| `app_env`        | Environment tag in release notes (e.g. QA, UAT, PROD) | No       | `QA`    |
| `displayVersion` | App version name                                      | No       | –       |
| `buildVersion`   | App build number                                      | No       | –       |
| `sa_key`         | Firebase Service Account JSON (string or base64)      | Yes      | –       |

### 🧪 Local Development & Testing
```pip install -r requirements.txt```


### Set env variables:

```shell 
export project_id=123456789
export app_id=1:123456789:android:abc
export app_env=QA
export displayVersion=1.0.2
export buildVersion=93
export sa_key='{"type":"service_account", ...}'

```

### Run:

```python main.py```

### 🔍 How Selection Works

| Scenario	                          |   Result                              |
| ----------------------------------- | ------------------------------------- |
| `Exact version + build found`       |   Uses it                             |
| `Version exists but build missing`  |   Uses latest build for given version |
| `Version not found` 	              |   Falls back to env based release     |
| `Env not found`	                  |   Fetches latest available apk        |
