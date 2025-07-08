from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from datetime import datetime
import os
import requests
  
class GmailService:
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("REDIRECT_URI")
        # Updated Google Calendar scopes to use the broader 'calendar' scope
        self.scopes = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/calendar' # Broader scope for all calendar functionalities
        ]
    
    def get_auth_url(self):
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.scopes
        )
        flow.redirect_uri = self.redirect_uri
        auth_url, _ = flow.authorization_url(
            prompt='consent',
            access_type='offline',
            include_granted_scopes='true'
        )
        return auth_url, flow
    
    def exchange_code_for_tokens(self, code):
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.scopes
        )
        flow.redirect_uri = self.redirect_uri
        flow.fetch_token(code=code)
        return flow.credentials
    
    def build_service(self, access_token, refresh_token, service_name='gmail', version='v1'):
        """
        Builds and returns a Google API service.
        Can build 'gmail' or 'calendar' service.
        """
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes
        )
        return build(service_name, version, credentials=credentials)
    
    def get_user_info(self, access_token):
        """Get user info from Google's userinfo endpoint"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None
    
    def list_messages(self, service, query='', max_results=50, label_ids=None):
        try:
            params = {
                'userId': 'me',
                'q': query,
                'maxResults': max_results
            }
            if label_ids:
                params['labelIds'] = label_ids
            
            results = service.users().messages().list(**params).execute()
            messages = results.get('messages', [])
            return messages
        except HttpError as e:
            print(f"Error listing messages: {e}")
            return []
    
    def get_message(self, service, message_id):
        try:
            message = service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
            return message
        except HttpError as e:
            print(f"Error getting message: {e}")
            return None
    
    def parse_message(self, message):
        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        
        # Extract headers
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        recipient = next((h['value'] for h in headers if h['name'] == 'To'), '')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        
        # Parse date
        received_at = datetime.now()
        try:
            import email.utils
            received_at = datetime.fromtimestamp(email.utils.mktime_tz(email.utils.parsedate_tz(date)))
        except:
            pass
        
        # Extract body
        body_text = ''
        body_html = ''
        
        def extract_body(part):
            nonlocal body_text, body_html
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    body_text = base64.urlsafe_b64decode(data).decode('utf-8')
            elif part.get('mimeType') == 'text/html':
                data = part.get('body', {}).get('data', '')
                if data:
                    body_html = base64.urlsafe_b64decode(data).decode('utf-8')
            elif part.get('parts'):
                for subpart in part['parts']:
                    extract_body(subpart)
        
        extract_body(payload)
        
        # Get label information
        label_ids = message.get('labelIds', [])
        
        return {
            'message_id': message['id'],
            'thread_id': message.get('threadId', ''),
            'subject': subject,
            'sender': sender,
            'recipient': recipient,
            'body_text': body_text,
            'body_html': body_html,
            'labels': json.dumps(label_ids),
            'received_at': received_at,
            'is_read': 'UNREAD' not in label_ids,
            'is_starred': 'STARRED' in label_ids
        }
    
    def send_email(self, service, to, subject, body, cc=None, bcc=None):
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            msg = MIMEText(body)
            message.attach(msg)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return result
        except HttpError as e:
            print(f"Error sending email: {e}")
            return None
    
    def create_draft(self, service, to, subject, body, cc=None, bcc=None):
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            msg = MIMEText(body)
            message.attach(msg)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            result = service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw_message}}
            ).execute()
            
            return result
        except HttpError as e:
            print(f"Error creating draft: {e}")
            return None
    
    def update_draft(self, service, draft_id, to, subject, body, cc=None, bcc=None):
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            msg = MIMEText(body)
            message.attach(msg)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            result = service.users().drafts().update(
                userId='me',
                id=draft_id,
                body={'message': {'raw': raw_message}}
            ).execute()
            
            return result
        except HttpError as e:
            print(f"Error updating draft: {e}")
            return None
    
    def delete_draft(self, service, draft_id):
        try:
            service.users().drafts().delete(userId='me', id=draft_id).execute()
            return True
        except HttpError as e:
            print(f"Error deleting draft: {e}")
            return False
    
    def send_draft(self, service, draft_id):
        try:
            result = service.users().drafts().send(
                userId='me',
                body={'id': draft_id}
            ).execute()
            return result
        except HttpError as e:
            print(f"Error sending draft: {e}")
            return None
    
    def modify_message(self, service, message_id, add_labels=None, remove_labels=None):
        try:
            body = {}
            if add_labels:
                body['addLabelIds'] = add_labels
            if remove_labels:
                body['removeLabelIds'] = remove_labels
            
            result = service.users().messages().modify(
                userId='me',
                id=message_id,
                body=body
            ).execute()
            return result
        except HttpError as e:
            print(f"Error modifying message: {e}")
            return None

    # --- Google Calendar Service Methods ---

    def create_calendar_event(self, service, event_data):
        """Creates a new event in the user's primary Google Calendar."""
        try:
            event = service.events().insert(calendarId='primary', body=event_data).execute()
            return event
        except HttpError as e:
            print(f"Error creating calendar event: {e}")
            return None

    def list_calendar_events(self, service, time_min=None, time_max=None, max_results=10, single_events=True, order_by='startTime'):
        """Lists events from the user's primary Google Calendar."""
        try:
            params = {
                'calendarId': 'primary',
                'timeMin': time_min,
                'timeMax': time_max,
                'maxResults': max_results,
                'singleEvents': single_events,
                'orderBy': order_by,
            }
            # Remove None values from params
            params = {k: v for k, v in params.items() if v is not None}
            
            events_result = service.events().list(**params).execute()
            events = events_result.get('items', [])
            return events
        except HttpError as e:
            print(f"Error listing calendar events: {e}")
            return []

    def get_calendar_event(self, service, event_id):
        """Retrieves a specific event from the user's primary Google Calendar."""
        try:
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            return event
        except HttpError as e:
            print(f"Error getting calendar event: {e}")
            return None

    def update_calendar_event(self, service, event_id, event_data):
        """Updates an existing event in the user's primary Google Calendar."""
        try:
            event = service.events().update(calendarId='primary', eventId=event_id, body=event_data).execute()
            return event
        except HttpError as e:
            print(f"Error updating calendar event: {e}")
            return None

    def delete_calendar_event(self, service, event_id):
        """Deletes an event from the user's primary Google Calendar."""
        try:
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            return True
        except HttpError as e:
            print(f"Error deleting calendar event: {e}")
            return False
