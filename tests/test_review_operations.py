import unittest
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from test_base import BaseJoggingTest
from database import get_db_cursor


class ReviewOperationsTest(BaseJoggingTest):
    """Test cases for review operations."""

    def setUp(self):
        """Set up test environment with routes and events."""
        super().setUp()

        self.route_name = "Test Review Route"
        self.distance = 4.2
        self.avg_pace = 6.5

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO joggingroute (RouteName, Distance, AvgPace) VALUES (%s, %s, %s)",
                (self.route_name, self.distance, self.avg_pace),
            )
            self.route_id = cursor.lastrowid

        self.event_name = "Test Review Event"
        self.event_date = datetime.now() - timedelta(days=7)
        self.max_participants = 15

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO joggingevent (EventName, EventDate, MaxParticipants) VALUES (%s, %s, %s)",
                (self.event_name, self.event_date, self.max_participants),
            )
            self.event_id = cursor.lastrowid

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO eventregistration (EventID, JoggerEmail) VALUES (%s, %s)",
                (self.event_id, self.test_jogger_email),
            )

    def test_create_route_review(self):
        """Test creating a route review."""
        before_reviews = self._check_table_state(
            "routereview",
            "RouteID = %s AND JoggerEmail = %s",
            (self.route_id, self.test_jogger_email),
        )

        rating = 4
        comment = "Great scenic route with moderate difficulty."

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO routereview (RouteID, JoggerEmail, Rating, Comment) VALUES (%s, %s, %s, %s)",
                (self.route_id, self.test_jogger_email, rating, comment),
            )
            review_id = cursor.lastrowid

        after_reviews = self._check_table_state(
            "routereview",
            "RouteID = %s AND JoggerEmail = %s",
            (self.route_id, self.test_jogger_email),
        )

        self.assertEqual(
            len(before_reviews), 0, "There should be no reviews before the operation"
        )
        self.assertEqual(
            len(after_reviews), 1, "There should be one review after the operation"
        )
        self.assertEqual(after_reviews[0]["JoggerEmail"], self.test_jogger_email)
        self.assertEqual(after_reviews[0]["RouteID"], self.route_id)
        self.assertEqual(after_reviews[0]["Rating"], rating)
        self.assertEqual(after_reviews[0]["Comment"], comment)

        self.route_review_id = after_reviews[0]["ReviewID"]

    def test_update_route_review(self):
        """Test updating a route review."""
        initial_rating = 3
        initial_comment = "Initial thoughts on this route."

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO routereview (RouteID, JoggerEmail, Rating, Comment) VALUES (%s, %s, %s, %s)",
                (
                    self.route_id,
                    self.test_jogger_email,
                    initial_rating,
                    initial_comment,
                ),
            )
            review_id = cursor.lastrowid

        before_review = self._check_table_state(
            "routereview", "ReviewID = %s", (review_id,)
        )[0]

        new_rating = 5
        new_comment = "Updated: This route is amazing after trying it again!"

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "UPDATE routereview SET Rating = %s, Comment = %s WHERE ReviewID = %s",
                (new_rating, new_comment, review_id),
            )

        after_review = self._check_table_state(
            "routereview", "ReviewID = %s", (review_id,)
        )[0]

        self.assertEqual(after_review["Rating"], new_rating)
        self.assertEqual(after_review["Comment"], new_comment)

    def test_delete_route_review(self):
        """Test deleting a route review."""
        rating = 2
        comment = "Review to be deleted"

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO routereview (RouteID, JoggerEmail, Rating, Comment) VALUES (%s, %s, %s, %s)",
                (self.route_id, self.test_jogger_email, rating, comment),
            )
            review_id = cursor.lastrowid

        before_state = self._check_table_state(
            "routereview", "ReviewID = %s", (review_id,)
        )

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute("DELETE FROM routereview WHERE ReviewID = %s", (review_id,))

        after_state = self._check_table_state(
            "routereview", "ReviewID = %s", (review_id,)
        )

        self.assertEqual(len(before_state), 1, "Review should exist before deletion")
        self.assertEqual(len(after_state), 0, "Review should not exist after deletion")

    def test_create_event_review(self):
        """Test creating an event review."""
        before_reviews = self._check_table_state(
            "eventreview",
            "EventID = %s AND JoggerEmail = %s",
            (self.event_id, self.test_jogger_email),
        )

        rating = 5
        comment = "Excellent event organization and atmosphere!"

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO eventreview (EventID, JoggerEmail, Rating, Comment) VALUES (%s, %s, %s, %s)",
                (self.event_id, self.test_jogger_email, rating, comment),
            )
            review_id = cursor.lastrowid

        after_reviews = self._check_table_state(
            "eventreview",
            "EventID = %s AND JoggerEmail = %s",
            (self.event_id, self.test_jogger_email),
        )

        self.assertEqual(
            len(before_reviews), 0, "There should be no reviews before the operation"
        )
        self.assertEqual(
            len(after_reviews), 1, "There should be one review after the operation"
        )
        self.assertEqual(after_reviews[0]["JoggerEmail"], self.test_jogger_email)
        self.assertEqual(after_reviews[0]["EventID"], self.event_id)
        self.assertEqual(after_reviews[0]["Rating"], rating)
        self.assertEqual(after_reviews[0]["Comment"], comment)

        self.event_review_id = after_reviews[0]["ReviewID"]

    def test_update_event_review(self):
        """Test updating an event review."""
        initial_rating = 3
        initial_comment = "Initial thoughts on this event."

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO eventreview (EventID, JoggerEmail, Rating, Comment) VALUES (%s, %s, %s, %s)",
                (
                    self.event_id,
                    self.test_jogger_email,
                    initial_rating,
                    initial_comment,
                ),
            )
            review_id = cursor.lastrowid

        before_review = self._check_table_state(
            "eventreview", "ReviewID = %s", (review_id,)
        )[0]

        new_rating = 4
        new_comment = "Updated: This event was better than I initially thought!"

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "UPDATE eventreview SET Rating = %s, Comment = %s WHERE ReviewID = %s",
                (new_rating, new_comment, review_id),
            )

        after_review = self._check_table_state(
            "eventreview", "ReviewID = %s", (review_id,)
        )[0]

        self.assertEqual(after_review["Rating"], new_rating)
        self.assertEqual(after_review["Comment"], new_comment)

    def test_delete_event_review(self):
        """Test deleting an event review."""
        rating = 2
        comment = "Event review to be deleted"

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO eventreview (EventID, JoggerEmail, Rating, Comment) VALUES (%s, %s, %s, %s)",
                (self.event_id, self.test_jogger_email, rating, comment),
            )
            review_id = cursor.lastrowid

        before_state = self._check_table_state(
            "eventreview", "ReviewID = %s", (review_id,)
        )

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute("DELETE FROM eventreview WHERE ReviewID = %s", (review_id,))

        after_state = self._check_table_state(
            "eventreview", "ReviewID = %s", (review_id,)
        )

        self.assertEqual(len(before_state), 1, "Review should exist before deletion")
        self.assertEqual(len(after_state), 0, "Review should not exist after deletion")

    def test_get_average_ratings(self):
        """Test getting average ratings for route and event."""
        route_ratings = [5, 4, 3, 5, 4]
        for i, rating in enumerate(route_ratings):
            jogger_email = f"test_jogger{i}@example.com"
            jogger_name = f"Test Jogger {i}"

            with get_db_cursor(commit=False, connection=self.connection) as cursor:
                cursor.execute(
                    "INSERT INTO jogger (Email, Name) VALUES (%s, %s)",
                    (jogger_email, jogger_name),
                )

            with get_db_cursor(commit=False, connection=self.connection) as cursor:
                cursor.execute(
                    "INSERT INTO routereview (RouteID, JoggerEmail, Rating, Comment) VALUES (%s, %s, %s, %s)",
                    (
                        self.route_id,
                        jogger_email,
                        rating,
                        f"Review {i} with rating {rating}",
                    ),
                )

        event_ratings = [5, 3, 4, 5, 5]
        for i, rating in enumerate(event_ratings):
            jogger_email = f"test_jogger{i}@example.com"

            with get_db_cursor(commit=False, connection=self.connection) as cursor:
                cursor.execute(
                    "INSERT INTO eventregistration (EventID, JoggerEmail) VALUES (%s, %s)",
                    (self.event_id, jogger_email),
                )

            with get_db_cursor(commit=False, connection=self.connection) as cursor:
                cursor.execute(
                    "INSERT INTO eventreview (EventID, JoggerEmail, Rating, Comment) VALUES (%s, %s, %s, %s)",
                    (
                        self.event_id,
                        jogger_email,
                        rating,
                        f"Event review {i} with rating {rating}",
                    ),
                )

        with get_db_cursor(connection=self.connection) as cursor:
            cursor.execute(
                "SELECT COUNT(*) as count, AVG(Rating) as average FROM routereview WHERE RouteID = %s",
                (self.route_id,),
            )
            route_avg = cursor.fetchone()

        with get_db_cursor(connection=self.connection) as cursor:
            cursor.execute(
                "SELECT COUNT(*) as count, AVG(Rating) as average FROM eventreview WHERE EventID = %s",
                (self.event_id,),
            )
            event_avg = cursor.fetchone()

        self.assertEqual(route_avg["count"], len(route_ratings))
        self.assertEqual(event_avg["count"], len(event_ratings))
        self.assertAlmostEqual(float(route_avg["average"]), 4.2, places=1)
        self.assertAlmostEqual(float(event_avg["average"]), 4.4, places=1)


if __name__ == "__main__":
    unittest.main()
