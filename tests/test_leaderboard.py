import unittest
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from test_base import BaseJoggingTest
from database import get_db_cursor


class LeaderboardTest(BaseJoggingTest):
    """Test cases for leaderboard reports."""

    def setUp(self):
        """Set up test environment with an event and participants."""
        super().setUp()

        self.event_name = "Test Leaderboard Event"
        self.event_date = datetime.now() - timedelta(days=1)
        self.max_participants = 10

        with get_db_cursor(commit=False, connection=self.connection) as cursor:
            cursor.execute(
                "INSERT INTO joggingevent (EventName, EventDate, MaxParticipants) VALUES (%s, %s, %s)",
                (self.event_name, self.event_date, self.max_participants),
            )
            self.event_id = cursor.lastrowid

            cursor.execute(
                "INSERT INTO event_em (OrganizerEmail, EventID) VALUES (%s, %s)",
                (self.test_organizer_email, self.event_id),
            )

        self.test_joggers = []
        for i in range(5):
            jogger_email = f"test_jogger{i}@example.com"
            jogger_name = f"Test Jogger {i}"

            with get_db_cursor(commit=False, connection=self.connection) as cursor:
                cursor.execute(
                    "INSERT INTO jogger (Email, Name) VALUES (%s, %s)",
                    (jogger_email, jogger_name),
                )

            self.test_joggers.append({"email": jogger_email, "name": jogger_name})

            with get_db_cursor(commit=False, connection=self.connection) as cursor:
                cursor.execute(
                    "INSERT INTO eventregistration (EventID, JoggerEmail) VALUES (%s, %s)",
                    (self.event_id, jogger_email),
                )

    def test_leaderboard_generation(self):
        """Test that leaderboard is correctly generated from session data."""

        sessions = []
        for i, jogger in enumerate(self.test_joggers):
            start_dt = self.event_date + timedelta(hours=1)
            end_dt = start_dt + timedelta(minutes=30 + i * 10)
            distance = 5.0 - (i * 0.5)

            with get_db_cursor(commit=False, connection=self.connection) as cursor:
                cursor.execute(
                    "INSERT INTO jogging (StartDT, EndDT, Distance, JoggerEmail) VALUES (%s, %s, %s, %s)",
                    (start_dt, end_dt, distance, jogger["email"]),
                )
                session_id = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO eventsession (EventID, SessionID) VALUES (%s, %s)",
                    (self.event_id, session_id),
                )

            sessions.append(
                {"id": session_id, "email": jogger["email"], "distance": distance}
            )

        with get_db_cursor(connection=self.connection) as cursor:
            cursor.execute(
                """
                SELECT
                  je.EventID,
                  j.Name AS JoggerName,
                  j.Email AS JoggerEmail,
                  jog.Distance,
                  TIMESTAMPDIFF(SECOND, jog.StartDT, jog.EndDT) AS FinishTime,
                  RANK() OVER (PARTITION BY je.EventID ORDER BY jog.Distance DESC) AS `Rank`
                FROM eventsession je
                JOIN jogging jog ON je.SessionID = jog.SessionID
                JOIN jogger j ON jog.JoggerEmail = j.Email
                WHERE je.EventID = %s
                ORDER BY `Rank` ASC
            """,
                (self.event_id,),
            )
            leaderboard = cursor.fetchall()

        self.assertEqual(
            len(leaderboard),
            len(self.test_joggers),
            "Leaderboard should have an entry for each jogger",
        )

        for i, entry in enumerate(leaderboard):
            expected_distance = 5.0 - (i * 0.5)
            expected_rank = i + 1
            self.assertEqual(
                entry["Rank"],
                expected_rank,
                f"Entry at position {i} should have rank {expected_rank}",
            )
            self.assertEqual(
                entry["Distance"],
                expected_distance,
                f"Entry with rank {expected_rank} should have distance {expected_distance}",
            )

        jogger_emails = [j["email"] for j in self.test_joggers]
        leaderboard_emails = [entry["JoggerEmail"] for entry in leaderboard]

        jogger_emails.sort()
        leaderboard_emails.sort()

        self.assertEqual(
            sorted(leaderboard_emails),
            sorted(jogger_emails),
            "Leaderboard emails should match test jogger emails",
        )

    def test_jogger_ranking(self):
        """Test retrieving an individual jogger's ranking in an event."""

        for i, jogger in enumerate(self.test_joggers):
            start_dt = self.event_date + timedelta(hours=1)
            end_dt = start_dt + timedelta(minutes=30 + i * 10)
            distance = 5.0 - (i * 0.5)

            with get_db_cursor(commit=False, connection=self.connection) as cursor:
                cursor.execute(
                    "INSERT INTO jogging (StartDT, EndDT, Distance, JoggerEmail) VALUES (%s, %s, %s, %s)",
                    (start_dt, end_dt, distance, jogger["email"]),
                )
                session_id = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO eventsession (EventID, SessionID) VALUES (%s, %s)",
                    (self.event_id, session_id),
                )

        target_jogger = self.test_joggers[2]["email"]
        expected_rank = 3

        with get_db_cursor(connection=self.connection) as cursor:
            cursor.execute(
                """
                SELECT
                  je.EventID,
                  j.Name AS JoggerName,
                  j.Email AS JoggerEmail,
                  jog.Distance,
                  TIMESTAMPDIFF(SECOND, jog.StartDT, jog.EndDT) AS FinishTime,
                  RANK() OVER (PARTITION BY je.EventID ORDER BY jog.Distance DESC) AS `Rank`
                FROM eventsession je
                JOIN jogging jog ON je.SessionID = jog.SessionID
                JOIN jogger j ON jog.JoggerEmail = j.Email
                WHERE je.EventID = %s
                ORDER BY `Rank` ASC
            """,
                (self.event_id,),
            )
            all_rankings = cursor.fetchall()

        jogger_rank = None
        for ranking in all_rankings:
            if ranking["JoggerEmail"] == target_jogger:
                jogger_rank = ranking
                break

        self.assertIsNotNone(jogger_rank, "Should find the jogger in the leaderboard")
        self.assertEqual(
            jogger_rank["Rank"],
            expected_rank,
            f"Jogger {target_jogger} should have rank {expected_rank}",
        )
        self.assertEqual(
            jogger_rank["Distance"],
            4.0,
            f"Jogger {target_jogger} should have distance 4.0",
        )

    def test_top_performers_report(self):
        """Test generating a top performers report."""

        event_names = ["Test Event A", "Test Event B", "Test Event C"]
        event_ids = []

        for event_name in event_names:
            event_date = datetime.now() - timedelta(days=30)

            with get_db_cursor(commit=False, connection=self.connection) as cursor:
                cursor.execute(
                    "INSERT INTO joggingevent (EventName, EventDate, MaxParticipants) VALUES (%s, %s, %s)",
                    (event_name, event_date, 20),
                )
                event_id = cursor.lastrowid
                event_ids.append(event_id)

                cursor.execute(
                    "INSERT INTO event_em (OrganizerEmail, EventID) VALUES (%s, %s)",
                    (self.test_organizer_email, event_id),
                )

        total_distances = {}

        for event_id in event_ids:
            for i, jogger in enumerate(self.test_joggers):
                with get_db_cursor(commit=False, connection=self.connection) as cursor:
                    cursor.execute(
                        "INSERT INTO eventregistration (EventID, JoggerEmail) VALUES (%s, %s)",
                        (event_id, jogger["email"]),
                    )

                if i == 0:
                    distance = 10.0
                else:
                    distance = 5.0 - (i * 0.5)

                if jogger["email"] not in total_distances:
                    total_distances[jogger["email"]] = 0
                total_distances[jogger["email"]] += distance

                start_dt = datetime.now() - timedelta(days=29)
                end_dt = start_dt + timedelta(hours=1)

                with get_db_cursor(commit=False, connection=self.connection) as cursor:
                    cursor.execute(
                        "INSERT INTO jogging (StartDT, EndDT, Distance, JoggerEmail) VALUES (%s, %s, %s, %s)",
                        (start_dt, end_dt, distance, jogger["email"]),
                    )
                    session_id = cursor.lastrowid

                    cursor.execute(
                        "INSERT INTO eventsession (EventID, SessionID) VALUES (%s, %s)",
                        (event_id, session_id),
                    )

        with get_db_cursor(connection=self.connection) as cursor:
            cursor.execute(
                """
                SELECT 
                    j.Email as JoggerEmail,
                    j.Name,
                    SUM(jog.Distance) as TotalDistance,
                    COUNT(DISTINCT es.EventID) as EventCount
                FROM eventsession es
                JOIN jogging jog ON es.SessionID = jog.SessionID
                JOIN jogger j ON jog.JoggerEmail = j.Email
                WHERE es.EventID IN ({})
                GROUP BY j.Email, j.Name
                ORDER BY TotalDistance DESC
                LIMIT 3
            """.format(
                    ",".join(["%s"] * len(event_ids))
                ),
                tuple(event_ids),
            )
            top_performers = cursor.fetchall()

        self.assertEqual(
            len(top_performers),
            min(3, len(self.test_joggers)),
            "Should have top 3 performers (or all joggers if fewer)",
        )

        self.assertEqual(
            top_performers[0]["JoggerEmail"],
            self.test_joggers[0]["email"],
            "First jogger should be the top performer",
        )
        self.assertEqual(
            top_performers[0]["TotalDistance"],
            10.0 * len(event_ids),
            f"Top performer should have 10km x {len(event_ids)} events = {10.0 * len(event_ids)}km",
        )
        self.assertEqual(
            top_performers[0]["EventCount"],
            len(event_ids),
            f"Top performer should have participated in all {len(event_ids)} events",
        )


if __name__ == "__main__":
    unittest.main()
