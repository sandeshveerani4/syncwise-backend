from __future__ import annotations

from typing import TYPE_CHECKING, List

from langchain_core.tools import BaseTool
from langchain_core.tools.base import BaseToolkit
from pydantic import ConfigDict, Field

from langchain_google_community.calendar.current_datetime import GetCurrentDatetime
from langchain_google_community.calendar.delete_event import CalendarDeleteEvent
from langchain_google_community.calendar.get_calendars_info import GetCalendarsInfo
from langchain_google_community.calendar.move_event import CalendarMoveEvent
from langchain_google_community.calendar.update_event import CalendarUpdateEvent
from langchain_google_community.calendar.utils import build_resource_service
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union
from uuid import uuid4

from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from langchain_google_community.calendar.base import CalendarBaseTool
from langchain_google_community.calendar.utils import is_all_day_event
import json

class CreateEventSchema(BaseModel):
    """Input for CalendarCreateEvent."""

    summary: str = Field(..., description="The title of the event.")
    start_datetime: str = Field(
        ...,
        description=(
            "The start datetime for the event in 'YYYY-MM-DD HH:MM:SS' format."
            "If the event is an all-day event, set the time to 'YYYY-MM-DD' format."
            "If you do not know the current datetime, use the tool to get it."
        ),
    )
    end_datetime: str = Field(
        ...,
        description=(
            "The end datetime for the event in 'YYYY-MM-DD HH:MM:SS' format. "
            "If the event is an all-day event, set the time to 'YYYY-MM-DD' format."
        ),
    )
    timezone: str = Field(..., description="The timezone of the event.")
    calendar_id: str = Field(
        default="primary", description="The calendar ID to create the event in."
    )
    recurrence: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "The recurrence of the event. "
            "Format: {'FREQ': <'DAILY' or 'WEEKLY'>, 'INTERVAL': <number>, "
            "'COUNT': <number or None>, 'UNTIL': <'YYYYMMDD' or None>, "
            "'BYDAY': <'MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU' or None>}. "
            "Use either COUNT or UNTIL, but not both; set the other to None."
        ),
    )
    location: Optional[str] = Field(
        default=None, description="The location of the event."
    )
    description: Optional[str] = Field(
        default=None, description="The description of the event."
    )
    attendees: Optional[List[str]] = Field(
        default=None, description="A list of attendees' email addresses for the event."
    )
    reminders: Union[None, bool, List[Dict[str, Any]]] = Field(
        default=None,
        description=(
            "Reminders for the event. "
            "Set to True for default reminders, or provide a list like "
            "[{'method': 'email', 'minutes': <minutes>}, ...]. "
            "Valid methods are 'email' and 'popup'."
        ),
    )
    conference_data: Optional[bool] = Field(
        default=None, description="Whether to include conference data."
    )
    color_id: Optional[str] = Field(
        default=None,
        description=(
            "The color ID of the event. None for default. "
            "'1': Lavender, '2': Sage, '3': Grape, '4': Flamingo, '5': Banana, "
            "'6': Tangerine, '7': Peacock, '8': Graphite, '9': Blueberry, "
            "'10': Basil, '11': Tomato."
        ),
    )
    transparency: Optional[str] = Field(
        default=None,
        description=(
            "User availability for the event."
            "transparent for available and opaque for busy."
        ),
    )


class CalendarCreateEvent(CalendarBaseTool):  # type: ignore[override, override]
    """Tool that creates an event in Google Calendar."""

    name: str = "create_calendar_event"
    description: str = (
        "Use this tool to create an event. "
        "The input must include the summary, start, and end datetime for the event."
    )
    args_schema: Type[CreateEventSchema] = CreateEventSchema

    def _prepare_event(
        self,
        summary: str,
        start_datetime: str,
        end_datetime: str,
        timezone: str,
        recurrence: Optional[Dict[str, Any]] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        reminders: Union[None, bool, List[Dict[str, Any]]] = None,
        conference_data: Optional[bool] = None,
        color_id: Optional[str] = None,
        transparency: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Prepare the event body."""
        try:
            if is_all_day_event(start_datetime, end_datetime):
                start = {"date": start_datetime}
                end = {"date": end_datetime}
            else:
                datetime_format = "%Y-%m-%d %H:%M:%S"
                start_dt = datetime.strptime(start_datetime, datetime_format)
                end_dt = datetime.strptime(end_datetime, datetime_format)
                start = {
                    "dateTime": start_dt.astimezone().isoformat(),
                    "timeZone": timezone,
                }
                end = {
                    "dateTime": end_dt.astimezone().isoformat(),
                    "timeZone": timezone,
                }
        except ValueError as error:
            raise ValueError("The datetime format is incorrect.") from error
        recurrence_data = None
        if recurrence:
            if isinstance(recurrence, dict):
                recurrence_items = [
                    f"{k}={v}" for k, v in recurrence.items() if v is not None
                ]
                recurrence_data = "RRULE:" + ";".join(recurrence_items)
        attendees_emails: List[Dict[str, str]] = []
        if attendees:
            email_pattern = r"^[^@]+@[^@]+\.[^@]+$"
            for email in attendees:
                if not re.match(email_pattern, email):
                    raise ValueError(f"Invalid email address: {email}")
                attendees_emails.append({"email": email})
        reminders_info: Dict[str, Union[bool, List[Dict[str, Any]]]] = {}
        if reminders is True:
            reminders_info.update({"useDefault": True})
        elif isinstance(reminders, list):
            for reminder in reminders:
                if "method" not in reminder or "minutes" not in reminder:
                    raise ValueError(
                        "Each reminder must have 'method' and 'minutes' keys."
                    )
                if reminder["method"] not in ["email", "popup"]:
                    raise ValueError("The reminder method must be 'email' or 'popup")
            reminders_info.update({"useDefault": False, "overrides": reminders})
        else:
            reminders_info.update({"useDefault": False})
        conference_data_info = None
        if conference_data:
            conference_data_info = {
                "createRequest": {
                    "requestId": str(uuid4()),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }
        event_body: Dict[str, Any] = {"summary": summary, "start": start, "end": end}
        if location:
            event_body["location"] = location
        if description:
            event_body["description"] = description
        if recurrence_data:
            event_body["recurrence"] = [recurrence_data]
        if len(attendees_emails) > 0:
            event_body["attendees"] = attendees_emails
        if len(reminders_info) > 0:
            event_body["reminders"] = reminders_info
        if conference_data_info:
            event_body["conferenceData"] = conference_data_info
        if color_id:
            event_body["colorId"] = color_id
        if transparency:
            event_body["transparency"] = transparency
        return event_body

    def _run(
        self,
        summary: str,
        start_datetime: str,
        end_datetime: str,
        timezone: str,
        calendar_id: str = "primary",
        recurrence: Optional[Dict[str, Any]] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        reminders: Union[None, bool, List[Dict[str, Any]]] = None,
        conference_data: Optional[bool] = None,
        color_id: Optional[str] = None,
        transparency: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Run the tool to create an event in Google Calendar."""
        try:
            body = self._prepare_event(
                summary=summary,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                timezone=timezone,
                recurrence=recurrence,
                location=location,
                description=description,
                attendees=attendees,
                reminders=reminders,
                conference_data=conference_data,
                color_id=color_id,
                transparency=transparency,
            )
            conference_version = 1 if conference_data else 0
            event = (
                self.api_resource.events()
                .insert(
                    calendarId=calendar_id,
                    body=body,
                    conferenceDataVersion=conference_version,
                )
                .execute()
            )
            return f"Event created: {event.get('htmlLink')}"
        except Exception as error:
            raise Exception(f"An error occurred: {error}") from error

from zoneinfo import ZoneInfo


class SearchEventsSchema(BaseModel):
    """Input for CalendarSearchEvents."""

    calendars_info: str = Field(
        ...,
        description=(
            "A list in json string with the information about all Calendars in Google Calendar"
            "Use the tool 'get_calendars_info' to get it."
        ),
    )
    min_datetime: str = Field(
        ...,
        description=(
            "The start datetime for the events in 'YYYY-MM-DD HH:MM:SS' format. "
            "If you do not know the current datetime, use the tool to get it."
        ),
    )
    max_datetime: str = Field(
        ..., description="The end datetime for the events search."
    )
    max_results: int = Field(
        default=10, description="The maximum number of results to return."
    )
    single_events: bool = Field(
        default=True,
        description=(
            "Whether to expand recurring events into instances and only return single "
            "one-off events and instances of recurring events."
            "'startTime' or 'updated'."
        ),
    )
    order_by: str = Field(
        default="startTime",
        description="The order of the events, either 'startTime' or 'updated'.",
    )
    query: Optional[str] = Field(
        default=None,
        description=(
            "Free text search terms to find events, "
            "that match these terms in the following fields: "
            "summary, description, location, attendee's displayName, attendee's email, "
            "organizer's displayName, organizer's email."
        ),
    )


class CalendarSearchEvents(CalendarBaseTool):  # type: ignore[override, override]
    """Tool that retrieves events from Google Calendar."""

    name: str = "search_events"
    description: str = "Use this tool to search events in the calendar."
    args_schema: Type[SearchEventsSchema] = SearchEventsSchema

    def _get_calendar_timezone(
        self, calendars_info: List[Dict[str, str]], calendar_id: str
    ) -> Optional[str]:
        """Get the timezone of the current calendar."""
        for cal in calendars_info:
            if cal["id"] == calendar_id:
                return cal.get("timeZone")
        return None

    def _get_calendar_ids(self, calendars_info: List[Dict[str, str]]) -> List[str]:
        """Get the calendar IDs."""
        return [cal["id"] for cal in calendars_info]

    def _process_data_events(
        self, events_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Optional[str]]]:
        """Process the data events."""
        simplified_data = []
        for data in events_data:
            event_dict = {
                "id": data.get("id"),
                "htmlLink": data.get("htmlLink"),
                "summary": data.get("summary"),
                "creator": data.get("creator", {}).get("email"),
                "organizer": data.get("organizer", {}).get("email"),
                "start": data.get("start", {}).get("dateTime")
                or data.get("start", {}).get("date"),
                "end": data.get("end", {}).get("dateTime")
                or data.get("end", {}).get("date"),
            }
            simplified_data.append(event_dict)
        return json.dumps(simplified_data)

    def _run(
        self,
        calendars_info: str,
        min_datetime: str,
        max_datetime: str,
        max_results: int = 10,
        single_events: bool = True,
        order_by: str = "startTime",
        query: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> List[Dict[str, Optional[str]]]:
        """Run the tool to search events in Google Calendar."""
        try:
            calendars_data = json.loads(calendars_info)
            calendars = self._get_calendar_ids(calendars_data)
            events = []
            for calendar in calendars:
                tz_name = self._get_calendar_timezone(calendars_data, calendar)
                calendar_tz = ZoneInfo(tz_name) if tz_name else None
                time_min = (
                    datetime.strptime(min_datetime, "%Y-%m-%d %H:%M:%S")
                    .astimezone(calendar_tz)
                    .isoformat()
                )
                time_max = (
                    datetime.strptime(max_datetime, "%Y-%m-%d %H:%M:%S")
                    .astimezone(calendar_tz)
                    .isoformat()
                )
                events_result = (
                    self.api_resource.events()
                    .list(
                        calendarId=calendar,
                        timeMin=time_min,
                        timeMax=time_max,
                        maxResults=max_results,
                        singleEvents=single_events,
                        orderBy=order_by,
                        q=query,
                    )
                    .execute()
                )
                cal_events = events_result.get("items", [])
                events.extend(cal_events)
            return self._process_data_events(events)
        except Exception as error:
            raise Exception(
                f"An error occurred while fetching events: {error}"
            ) from error

if TYPE_CHECKING:
    # This is for linting and IDE typehints
    from googleapiclient.discovery import Resource  # type: ignore[import]
else:
    try:
        # We do this so pydantic can resolve the types when instantiating
        from googleapiclient.discovery import Resource
    except ImportError:
        pass


SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarToolkit(BaseToolkit):
    """Toolkit for interacting with Google Calendar.

    *Security Note*: This toolkit contains tools that can read and modify
        the state of a service; e.g., by reading, creating, updating, deleting
        data associated with this service.

        For example, this toolkit can be used to create events on behalf of the
        associated account.

        See https://python.langchain.com/docs/security for more information.
    """

    api_resource: Resource = Field(default_factory=build_resource_service)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        return [
            CalendarCreateEvent(api_resource=self.api_resource),
            CalendarSearchEvents(api_resource=self.api_resource),
            CalendarUpdateEvent(api_resource=self.api_resource),
            GetCalendarsInfo(api_resource=self.api_resource),
            CalendarMoveEvent(api_resource=self.api_resource),
            CalendarDeleteEvent(api_resource=self.api_resource),
            GetCurrentDatetime(api_resource=self.api_resource),
        ]
