import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Replace this with your JSON string (ensure it's exact, with \n in private_key)
service_account_json = '''{
  "type": "service_account",
  "project_id": "pdf-tool-logs",
  "private_key_id": "c312c4041ead7955e25b0cef22f60197e716cb89",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCak/25ez56zTNn\\n0aFfGn2v4Tot/hUOwDj+xrz/0MGtTcFsmRAd7RUsAJRwc0NBAZCZZaoihj/leEO5\\n...\\n-----END PRIVATE KEY-----\\n",
  "client_email": "website@pdf-tool-logs.iam.gserviceaccount.com",
  "client_id": "100722900645678398047",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/website%40pdf-tool-logs.iam.gserviceaccount.com"
}'''

# Load JSON
try:
    credentials_info = json.loads(service_account_json)
except json.JSONDecodeError as e:
    print("JSON is invalid:", e)
    exit()

# Create credentials
try:
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    print("✅ Service account JSON is valid and credentials object created.")
except Exception as e:
    print("❌ Error creating credentials:", e)
    exit()

# Optional: Test access by listing GCP projects
try:
    service = build('cloudresourcemanager', 'v1', credentials=credentials)
    projects = service.projects().list().execute()
    print("✅ Authentication successful! Projects accessible:")
    for proj in projects.get('projects', []):
        print("-", proj['projectId'])
except Exception as e:
    print("❌ Authentication failed or no projects accessible:", e)
