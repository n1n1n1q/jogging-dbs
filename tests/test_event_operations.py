import unittest
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from test_base import BaseJoggingTest
from database import get_db_cursor

from models.repositories import EventRepository, RegistrationRepository


class EventOperationsTest(BaseJoggingTest):
    """Test cases for event operations."""

    def test_create_event(self):
        """Test creating a new event."""
        before_events = self._check_table_state(
            "joggingevent", "EventName LIKE 'Test Event%'"
        )

        event_name = "Test Event 1"
        event_date = datetime.now() + timedelta(days=30)
        max_participants = 50

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO joggingevent (EventName, EventDate, MaxParticipants) VALUES (%s, %s, %s)",
                (event_name, event_date, max_participants),
            )
            event_id = cursor.lastrowid

            cursor.execute(
                "INSERT INTO event_em (OrganizerEmail, EventID) VALUES (%s, %s)",
                (self.test_organizer_email, event_id),
            )

        after_events = self._check_table_state(
            "joggingevent", "EventName LIKE 'Test Event%'"
        )

        self.assertEqual(
            len(before_events), 0, "There should be no test events before the operation"
        )
        self.assertEqual(
            len(after_events), 1, "There should be one test event after the operation"
        )
        self.assertEqual(after_events[0]["EventName"], event_name)
        self.assertEqual(after_events[0]["MaxParticipants"], max_participants)

        self.event_id = event_id

    def test_update_event(self):
        """Test updating an existing event."""
        event_name = "Test Event Update"
        event_date = datetime.now() + timedelta(days=60)
        max_participants = 30

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO joggingevent (EventName, EventDate, MaxParticipants) VALUES (%s, %s, %s)",
                (event_name, event_date, max_participants),
            )
            event_id = cursor.lastrowid

        before_event = self._check_table_state(
            "joggingevent", "EventID = %s", (event_id,)
        )[0]

        new_event_date = datetime.now() + timedelta(days=90)
        new_max_participants = 40

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "UPDATE joggingevent SET EventDate = %s, MaxParticipants = %s WHERE EventID = %s",
                (new_event_date, new_max_participants, event_id),
            )

        after_event = self._check_table_state(
            "joggingevent", "EventID = %s", (event_id,)
        )[0]

        self.assertEqual(after_event["EventName"], event_name)
        self.assertEqual(after_event["MaxParticipants"], new_max_participants)
        self.assertLessEqual(
            abs((after_event["EventDate"] - new_event_date).total_seconds()),
            1,
            "The event date should be updated correctly",
        )

    def test_delete_event(self):
        """Test deleting an event."""
        event_name = "Test Event Delete"
        event_date = datetime.now() + timedelta(days=45)
        max_participants = 25

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO joggingevent (EventName, EventDate, MaxParticipants) VALUES (%s, %s, %s)",
                (event_name, event_date, max_participants),
            )
            event_id = cursor.lastrowid

        before_state = self._check_table_state(
            "joggingevent", "EventID = %s", (event_id,)
        )

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute("DELETE FROM joggingevent WHERE EventID = %s", (event_id,))

        after_state = self._check_table_state(
            "joggingevent", "EventID = %s", (event_id,)
        )

        self.assertEqual(len(before_state), 1, "Event should exist before deletion")
        self.assertEqual(len(after_state), 0, "Event should not exist after deletion")

    def test_event_registration(self):
        """Test registering and unregistering a jogger for an event."""
        event_name = "Test Event Registration"
        event_date = datetime.now() + timedelta(days=30)
        max_participants = 10

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO joggingevent (EventName, EventDate, MaxParticipants) VALUES (%s, %s, %s)",
                (event_name, event_date, max_participants),
            )
            event_id = cursor.lastrowid

        before_registrations = self._check_table_state(
            "eventregistration",
            "EventID = %s AND JoggerEmail = %s",
            (event_id, self.test_jogger_email),
        )

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO eventregistration (EventID, JoggerEmail) VALUES (%s, %s)",
                (event_id, self.test_jogger_email),
            )

        mid_registrations = self._check_table_state(
            "eventregistration",
            "EventID = %s AND JoggerEmail = %s",
            (event_id, self.test_jogger_email),
        )

        self.assertEqual(
            len(before_registrations), 0, "Should not be registered before operation"
        )
        self.assertEqual(
            len(mid_registrations), 1, "Should be registered after operation"
        )

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "DELETE FROM eventregistration WHERE EventID = %s AND JoggerEmail = %s",
                (event_id, self.test_jogger_email),
            )

        after_registrations = self._check_table_state(
            "eventregistration",
            "EventID = %s AND JoggerEmail = %s",
            (event_id, self.test_jogger_email),
        )

        self.assertEqual(
            len(after_registrations), 0, "Should not be registered after unregistration"
        )


if __name__ == "__main__":
    unittest.main()
