import unittest
import sys
import os
from datetime import datetime
import mysql.connector

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))

from database import get_db_connection, get_db_cursor, DB_CONFIG
from models.repositories import (
    JoggerRepository,
    RouteRepository,
    EventRepository,
    RegistrationRepository,
    JoggingSessionRepository,
    ReviewRepository,
    LeaderboardRepository,
)


class BaseJoggingTest(unittest.TestCase):
    """Base class for jogging app tests."""

    def setUp(self):
        """Set up test environment."""
        self.connection = mysql.connector.connect(**DB_CONFIG)
        self.connection.autocommit = False

        self.test_jogger_email = "test_jogger@example.com"
        self.test_jogger_name = "Test Jogger"
        self.test_organizer_email = "test_organizer@example.com"
        self.test_organizer_name = "Test Organizer"
        self.test_admin_email = "test_admin@example.com"

        self._clean_test_data()
        self._create_test_data()

    def tearDown(self):
        """Clean up after tests by rolling back the transaction."""
        if hasattr(self, "connection") and self.connection:
            self.connection.rollback()
            self.connection.close()

    def _clean_test_data(self):
        """Clean up test data from database."""
        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "DELETE FROM eventreview WHERE JoggerEmail = %s",
                (self.test_jogger_email,),
            )
            cursor.execute(
                "DELETE FROM routereview WHERE JoggerEmail = %s",
                (self.test_jogger_email,),
            )
            cursor.execute(
                "DELETE FROM eventsession WHERE SessionID IN (SELECT SessionID FROM jogging WHERE JoggerEmail = %s)",
                (self.test_jogger_email,),
            )
            cursor.execute(
                "DELETE FROM eventregistration WHERE JoggerEmail = %s",
                (self.test_jogger_email,),
            )
            cursor.execute(
                "DELETE FROM jogging WHERE JoggerEmail = %s", (self.test_jogger_email,)
            )
            cursor.execute(
                "DELETE FROM jogger WHERE Email = %s", (self.test_jogger_email,)
            )

            cursor.execute(
                "DELETE FROM event_em WHERE OrganizerEmail = %s",
                (self.test_organizer_email,),
            )
            cursor.execute(
                "DELETE FROM eventorganizer WHERE Email = %s",
                (self.test_organizer_email,),
            )

            cursor.execute(
                "DELETE FROM route_admin WHERE AdminEmail = %s",
                (self.test_admin_email,),
            )
            cursor.execute(
                "DELETE FROM appadmin WHERE AdminEmail = %s", (self.test_admin_email,)
            )

            cursor.execute(
                "DELETE FROM joggingevent WHERE EventName LIKE %s", ("Test Event%",)
            )

            cursor.execute(
                "DELETE FROM joggingroute WHERE RouteName LIKE %s", ("Test Route%",)
            )

    def _create_test_data(self):
        """Create test data for tests."""
        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO jogger (Email, Name) VALUES (%s, %s)",
                (self.test_jogger_email, self.test_jogger_name),
            )

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO eventorganizer (Email, Name) VALUES (%s, %s)",
                (self.test_organizer_email, self.test_organizer_name),
            )

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO appadmin (AdminEmail) VALUES (%s)",
                (self.test_admin_email,),
            )

    def _check_table_state(self, table_name, where_clause=None, params=None):
        """Get the current state of a table with optional filtering."""
        query = f"SELECT * FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"

        with get_db_cursor(connection=self.connection) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()


if __name__ == "__main__":
    unittest.main()
