from googleapiclient.errors import HttpError

class CalendarService:
    def __init__(self):
        pass

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