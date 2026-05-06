import os
import json
import re
import html
import asyncio

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

from django.conf import settings
from .vectorizer import Vectorization
from sementicsearchemails.utils import decode_base64

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class RAG_Gmail:

    def __init__(self, user, base_url: str = "/"):
        self._user = user
        self._vectorizer = Vectorization(user)
        self._base_url = base_url
        os.makedirs(os.path.join(settings.BASE_DIR, 'secrets', 'users'), exist_ok=True)

    def _get_gmail_service(self):
        creds = None
        if os.path.exists(f'secrets/users/{self._user.id}-token.json'):
            file_path = os.path.join(settings.BASE_DIR, "secrets", "users", f"{self._user.id}-token.json")
            creds = Credentials.from_authorized_user_file(file_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                file_path = os.path.join(settings.BASE_DIR, "secrets", "credentials.json")
                flow = InstalledAppFlow.from_client_secrets_file(file_path, SCOPES)
                creds = flow.run_local_server(
                    port=8080,
                    access_type="offline",
                    prompt="consent"
                )

            file_path = os.path.join(settings.BASE_DIR, "secrets", "users", f"{self._user.id}-token.json")
            with open(file_path, 'w') as token:
                token.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds)

    async def read_emails(self):
        service = self._get_gmail_service()
        results = service.users().messages().list(userId='me', maxResults=100).execute()
        messages = results.get('messages', [])

        results = {
            "ids": [],
            "documents": [],
            "embeddings": [],
            "metadatas": []
        }

        response_data = self._vectorizer._get_all_records()
        existing_ids = response_data

        response = await asyncio.gather(
            *(self._fetch_message(msg) for msg in messages if not existing_ids or msg['id'] not in existing_ids)
        )
 
        for i in response:
            if i is not None:
                results['ids'].append(i['id'])
                results['documents'].append(i['content'])
                results['embeddings'].append(i['embedding'])
                results['metadatas'].append(i['metadata'])

        if len(results['ids']) > 0:
            self._vectorizer.vectorize_raw_data(results)
            return response
    
    async def _fetch_message(self, msg):
        service = self._get_gmail_service()
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = msg_data['payload']['headers']
        
        for h in headers:
            if h['name'] == 'Subject':
                subject = h['value']
            if h['name'] == 'From':
                from_mail = h['value']
            if h['name'] == 'To':
                to_mail = h['value']
            if h['name'] == 'Date':
                mail_date = h['value']

        body = self._get_email_body(msg_data['payload'])
        body = self._clean_email_text(body)
        body = self._html_to_text(body)

        if len(body) < 100:
            return
        id = f"{msg_data['id']}-{msg_data['threadId']}"
        
        content = f"{subject}\n{body}"
        return {
            "id": id,
            'content': content,
            "embedding": self._vectorizer.transform(content),
            "metadata": {
                "thread_id": msg_data['threadId'],
                "labels": msg_data['labelIds'],
                "From": from_mail,
                "To": to_mail,
                "Date": mail_date
            }
        }

        
    def _save_single_file(self, item):
        with open(item['file_path'], "w", encoding="utf-8") as email:
            json.dump(item['data'], email)

    def _get_email_body(self, payload):
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType')

                # Prefer plain text
                if mime_type == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        return decode_base64(data)

            # Fallback to HTML
            for part in payload['parts']:
                if part.get('mimeType') == 'text/html':
                    data = part['body'].get('data')
                    if data:
                        return decode_base64(data)

        else:
            data = payload.get('body', {}).get('data')
            if data:
                return decode_base64(data)

        return ""
    
    def _clean_email_text(self, text):
        text = html.unescape(text)
        text = text.replace('\r\n', '\n')
        text = re.sub(r'^\s*>+\s?', '', text, flags=re.MULTILINE)
        text = text.replace('\ufeff', '')
        text = text.replace('\u202f', ' ')
        text = re.sub(r"(fwd:|re:)", "", text)
        text = re.sub(r"cheers.*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r'\n+', '\n', text)

        return text.strip()
    
    def _html_to_text(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text()