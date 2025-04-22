import unittest
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from test_base import BaseJoggingTest
from database import get_db_cursor

from models.repositories import RouteRepository


class RouteOperationsTest(BaseJoggingTest):
    """Test cases for route operations."""

    def test_create_route(self):
        """Test creating a new route."""
        before_routes = self._check_table_state(
            "joggingroute", "RouteName LIKE 'Test Route%'"
        )

        route_name = "Test Route 1"
        distance = 5.5
        avg_pace = 8.2

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO joggingroute (RouteName, Distance, AvgPace) VALUES (%s, %s, %s)",
                (route_name, distance, avg_pace),
            )
            route_id = cursor.lastrowid

        after_routes = self._check_table_state(
            "joggingroute", "RouteName LIKE 'Test Route%'"
        )

        self.assertEqual(
            len(before_routes), 0, "There should be no test routes before the operation"
        )
        self.assertEqual(
            len(after_routes), 1, "There should be one test route after the operation"
        )
        self.assertEqual(after_routes[0]["RouteName"], route_name)
        self.assertEqual(after_routes[0]["Distance"], distance)
        self.assertEqual(after_routes[0]["AvgPace"], avg_pace)

        self.route_id = route_id

    def test_update_route(self):
        """Test updating an existing route."""
        route_name = "Test Route Update"
        distance = 3.2
        avg_pace = 7.5

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO joggingroute (RouteName, Distance, AvgPace) VALUES (%s, %s, %s)",
                (route_name, distance, avg_pace),
            )
            route_id = cursor.lastrowid

        before_route = self._check_table_state(
            "joggingroute", "RouteID = %s", (route_id,)
        )[0]

        new_distance = 4.8
        new_avg_pace = 6.9

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "UPDATE joggingroute SET Distance = %s, AvgPace = %s WHERE RouteID = %s",
                (new_distance, new_avg_pace, route_id),
            )

        after_route = self._check_table_state(
            "joggingroute", "RouteID = %s", (route_id,)
        )[0]

        self.assertEqual(after_route["RouteName"], route_name)
        self.assertEqual(after_route["Distance"], new_distance)
        self.assertEqual(after_route["AvgPace"], new_avg_pace)

    def test_delete_route(self):
        """Test deleting a route."""
        route_name = "Test Route Delete"
        distance = 2.7
        avg_pace = 8.0

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO joggingroute (RouteName, Distance, AvgPace) VALUES (%s, %s, %s)",
                (route_name, distance, avg_pace),
            )
            route_id = cursor.lastrowid

        before_state = self._check_table_state(
            "joggingroute", "RouteID = %s", (route_id,)
        )

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute("DELETE FROM joggingroute WHERE RouteID = %s", (route_id,))

        after_state = self._check_table_state(
            "joggingroute", "RouteID = %s", (route_id,)
        )

        self.assertEqual(len(before_state), 1, "Route should exist before deletion")
        self.assertEqual(len(after_state), 0, "Route should not exist after deletion")


if __name__ == "__main__":
    unittest.main()
