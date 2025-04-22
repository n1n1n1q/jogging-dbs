import unittest
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from test_base import BaseJoggingTest
from database import get_db_cursor

class SessionOperationsTest(BaseJoggingTest):
    """Test cases for jogging session operations."""

    def setUp(self):
        """Set up test environment with a route and event."""
        super().setUp()
        
        self.route_name = "Test Session Route"
        self.distance = 3.5
        self.avg_pace = 7.8
        
        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO joggingroute (RouteName, Distance, AvgPace) VALUES (%s, %s, %s)",
                (self.route_name, self.distance, self.avg_pace)
            )
            self.route_id = cursor.lastrowid
        
        self.event_name = "Test Session Event"
        self.event_date = datetime.now() + timedelta(days=7)
        self.max_participants = 20
        
        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO joggingevent (EventName, EventDate, MaxParticipants) VALUES (%s, %s, %s)",
                (self.event_name, self.event_date, self.max_participants)
            )
            self.event_id = cursor.lastrowid

    def test_create_session(self):
        """Test creating a new jogging session."""
        before_sessions = self._check_table_state(
            "jogging", 
            "JoggerEmail = %s", 
            (self.test_jogger_email,)
        )
        
        start_dt = datetime.now() - timedelta(hours=1)
        end_dt = datetime.now() - timedelta(minutes=30)
        distance = 2.5
        
        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO jogging (StartDT, EndDT, Distance, JoggerEmail, RouteID) VALUES (%s, %s, %s, %s, %s)",
                (start_dt, end_dt, distance, self.test_jogger_email, self.route_id)
            )
            session_id = cursor.lastrowid
        
        after_sessions = self._check_table_state(
            "jogging", 
            "JoggerEmail = %s", 
            (self.test_jogger_email,)
        )
        
        self.assertEqual(len(before_sessions), 0, "There should be no sessions before the operation")
        self.assertEqual(len(after_sessions), 1, "There should be one session after the operation")
        self.assertEqual(after_sessions[0]['JoggerEmail'], self.test_jogger_email)
        self.assertEqual(after_sessions[0]['Distance'], distance)
        self.assertEqual(after_sessions[0]['RouteID'], self.route_id)
        
        self.session_id = session_id
        
    def test_update_session(self):
        """Test updating a jogging session."""
        start_dt = datetime.now() - timedelta(hours=2)
        end_dt = datetime.now() - timedelta(hours=1)
        distance = 3.0
        
        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO jogging (StartDT, EndDT, Distance, JoggerEmail) VALUES (%s, %s, %s, %s)",
                (start_dt, end_dt, distance, self.test_jogger_email)
            )
            session_id = cursor.lastrowid
        
        before_session = self._check_table_state("jogging", "SessionID = %s", (session_id,))[0]
        
        new_distance = 3.5
        
        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "UPDATE jogging SET Distance = %s, RouteID = %s WHERE SessionID = %s",
                (new_distance, self.route_id, session_id)
            )
        
        after_session = self._check_table_state("jogging", "SessionID = %s", (session_id,))[0]
        
        self.assertEqual(after_session['Distance'], new_distance)
        self.assertEqual(after_session['RouteID'], self.route_id)
        
    def test_delete_session(self):
        """Test deleting a jogging session."""
        start_dt = datetime.now() - timedelta(hours=3)
        end_dt = datetime.now() - timedelta(hours=2)
        distance = 4.0
        
        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO jogging (StartDT, EndDT, Distance, JoggerEmail, RouteID) VALUES (%s, %s, %s, %s, %s)",
                (start_dt, end_dt, distance, self.test_jogger_email, self.route_id)
            )
            session_id = cursor.lastrowid
        
        before_state = self._check_table_state("jogging", "SessionID = %s", (session_id,))
        
        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute("DELETE FROM jogging WHERE SessionID = %s", (session_id,))
        
        after_state = self._check_table_state("jogging", "SessionID = %s", (session_id,))
        
        self.assertEqual(len(before_state), 1, "Session should exist before deletion")
        self.assertEqual(len(after_state), 0, "Session should not exist after deletion")

    def test_session_event_association(self):
        """Test associating and removing a session with an event."""
        start_dt = datetime.now() - timedelta(days=1)
        end_dt = start_dt + timedelta(minutes=45)
        distance = 5.0
        
        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO jogging (StartDT, EndDT, Distance, JoggerEmail, RouteID) VALUES (%s, %s, %s, %s, %s)",
                (start_dt, end_dt, distance, self.test_jogger_email, self.route_id)
            )
            session_id = cursor.lastrowid
        
        before_associations = self._check_table_state(
            "eventsession", 
            "EventID = %s AND SessionID = %s", 
            (self.event_id, session_id)
        )
        
        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO eventsession (EventID, SessionID) VALUES (%s, %s)",
                (self.event_id, session_id)
            )
        
        mid_associations = self._check_table_state(
            "eventsession", 
            "EventID = %s AND SessionID = %s", 
            (self.event_id, session_id)
        )
        
        self.assertEqual(len(before_associations), 0, "Association should not exist before operation")
        self.assertEqual(len(mid_associations), 1, "Association should exist after operation")
        
        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "DELETE FROM eventsession WHERE EventID = %s AND SessionID = %s",
                (self.event_id, session_id)
            )
        
        after_associations = self._check_table_state(
            "eventsession", 
            "EventID = %s AND SessionID = %s", 
            (self.event_id, session_id)
        )
        
        self.assertEqual(len(after_associations), 0, "Association should not exist after removal")


if __name__ == "__main__":
    unittest.main()