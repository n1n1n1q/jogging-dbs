from database import get_db_cursor


class BaseRepository:
    """Base repository with common database operations."""

    @staticmethod
    def execute_query(query, params=None, commit=False):
        """Execute a database query and return results."""
        print(f"Executing SQL: {query}")
        if params:
            print(f"Parameters: {params}")

            formatted_query = query
            if isinstance(params, (list, tuple)):
                for param in params:
                    if param is None:
                        formatted_value = "NULL"
                    elif isinstance(param, str):
                        formatted_value = f"'{param}'"
                    elif isinstance(param, (int, float)):
                        formatted_value = str(param)
                    else:
                        formatted_value = f"'{param}'"

                    formatted_query = formatted_query.replace("%s", formatted_value, 1)
            elif isinstance(params, dict):
                for key, value in params.items():
                    if value is None:
                        formatted_value = "NULL"
                    elif isinstance(value, str):
                        formatted_value = f"'{value}'"
                    elif isinstance(value, (int, float)):
                        formatted_value = str(value)
                    else:
                        formatted_value = f"'{value}'"

                    formatted_query = formatted_query.replace(
                        f"%({key})s", formatted_value
                    )

            print(f"Formatted SQL: {formatted_query}")

        with get_db_cursor(commit) as cursor:
            cursor.execute(query, params or ())
            if not commit:
                return cursor.fetchall()
            else:
                if (
                    "INSERT" in query.upper()
                    and "LAST_INSERT_ID()" not in query.upper()
                ):
                    cursor.execute("SELECT LAST_INSERT_ID() as id")
                    result = cursor.fetchone()
                    print(f"Generated ID: {result}")
                    return result
                return None


class JoggerRepository(BaseRepository):
    """Repository for jogger operations."""

    @staticmethod
    def get_jogger_by_email(email):
        """Get jogger by email."""
        query = "SELECT * FROM jogger WHERE Email = %s"
        result = BaseRepository.execute_query(query, (email,))
        print(query, result)
        return result[0] if result else None

    @staticmethod
    def create_jogger(email, name):
        """Create a new jogger."""
        query = "INSERT INTO jogger (Email, Name) VALUES (%s, %s)"
        BaseRepository.execute_query(query, (email, name), commit=True)

    @staticmethod
    def update_jogger(email, name):
        """Update jogger information."""
        query = "UPDATE jogger SET Name = %s WHERE Email = %s"
        BaseRepository.execute_query(query, (name, email), commit=True)

    @staticmethod
    def check_if_admin(email):
        """Check if the jogger is an admin."""
        query = "SELECT * FROM appadmin WHERE AdminEmail = %s"
        result = BaseRepository.execute_query(query, (email,))
        return bool(result)

    @staticmethod
    def check_if_organizer(email):
        """Check if the jogger is an event organizer."""
        query = "SELECT * FROM eventorganizer WHERE Email = %s"
        result = BaseRepository.execute_query(query, (email,))
        return bool(result)

    @staticmethod
    def get_organizer_name(email):
        """Get the name of an organizer by email."""
        query = "SELECT Name FROM eventorganizer WHERE Email = %s"
        result = BaseRepository.execute_query(query, (email,))
        return result[0]["Name"] if result else None


class RouteRepository(BaseRepository):
    """Repository for jogging route operations."""

    @staticmethod
    def get_all_routes():
        """Get all jogging routes."""
        query = "SELECT * FROM joggingroute"
        return BaseRepository.execute_query(query)

    @staticmethod
    def get_route_by_id(route_id):
        """Get a jogging route by ID."""
        query = "SELECT * FROM joggingroute WHERE RouteID = %s"
        result = BaseRepository.execute_query(query, (route_id,))
        return result[0] if result else None

    @staticmethod
    def create_route(route_name, distance, avg_pace=None):
        """Create a new jogging route."""
        query = "INSERT INTO joggingroute (RouteName, Distance, AvgPace) VALUES (%s, %s, %s)"
        return BaseRepository.execute_query(
            query, (route_name, distance, avg_pace), commit=True
        )["id"]

        # query = "SELECT LAST_INSERT_ID() as id"
        # result = BaseRepository.execute_query(query)
        # return result[0]['id'] if result else None

    @staticmethod
    def update_route(route_id, route_name, distance, avg_pace=None):
        """Update a jogging route."""
        query = "UPDATE joggingroute SET RouteName = %s, Distance = %s, AvgPace = %s WHERE RouteID = %s"
        print(query, route_name, distance, avg_pace, route_id)
        BaseRepository.execute_query(
            query, (route_name, distance, avg_pace, route_id), commit=True
        )

    @staticmethod
    def delete_route(route_id):
        """Delete a jogging route."""
        query = "DELETE FROM joggingroute WHERE RouteID = %s"
        BaseRepository.execute_query(query, (route_id,), commit=True)


class EventRepository(BaseRepository):
    """Repository for jogging event operations."""

    @staticmethod
    def get_all_events():
        """Get all jogging events."""
        query = "SELECT * FROM joggingevent ORDER BY EventDate"
        return BaseRepository.execute_query(query)

    @staticmethod
    def get_event_by_id(event_id):
        """Get a jogging event by ID."""
        query = "SELECT * FROM joggingevent WHERE EventID = %s"
        result = BaseRepository.execute_query(query, (event_id,))
        return result[0] if result else None

    @staticmethod
    def create_event(event_name, event_date, max_participants):
        """Create a new jogging event."""
        query = "INSERT INTO joggingevent (EventName, EventDate, MaxParticipants) VALUES (%s, %s, %s)"
        result = BaseRepository.execute_query(
            query, (event_name, event_date, max_participants), commit=True
        )

        if result and "id" in result:
            return result["id"]

        query = "SELECT LAST_INSERT_ID() as id"
        result = BaseRepository.execute_query(query)
        if result and result[0] and "id" in result[0]:
            return result[0]["id"]

        return None

    @staticmethod
    def update_event(event_id, event_name, event_date, max_participants):
        """Update a jogging event."""
        query = "UPDATE joggingevent SET EventName = %s, EventDate = %s, MaxParticipants = %s WHERE EventID = %s"
        BaseRepository.execute_query(
            query, (event_name, event_date, max_participants, event_id), commit=True
        )

    @staticmethod
    def delete_event(event_id):
        """Delete a jogging event."""
        query = "DELETE FROM joggingevent WHERE EventID = %s"
        BaseRepository.execute_query(query, (event_id,), commit=True)

    @staticmethod
    def get_events_by_organizer(organizer_email):
        """Get all events organized by a specific organizer."""
        query = """
        SELECT je.* FROM joggingevent je
        JOIN event_em em ON je.EventID = em.EventID
        WHERE em.OrganizerEmail = %s
        ORDER BY je.EventDate
        """
        return BaseRepository.execute_query(query, (organizer_email,))


class RegistrationRepository(BaseRepository):
    """Repository for event registration operations."""

    @staticmethod
    def register_for_event(event_id, jogger_email):
        """Register a jogger for an event."""
        query = "INSERT INTO eventregistration (EventID, JoggerEmail) VALUES (%s, %s)"
        BaseRepository.execute_query(query, (event_id, jogger_email), commit=True)

    @staticmethod
    def unregister_from_event(event_id, jogger_email):
        """Unregister a jogger from an event."""
        query = "DELETE FROM eventregistration WHERE EventID = %s AND JoggerEmail = %s"
        BaseRepository.execute_query(query, (event_id, jogger_email), commit=True)

    @staticmethod
    def get_event_registrations(event_id):
        """Get all registrations for an event."""
        query = """
        SELECT er.*, j.Name as JoggerName
        FROM eventregistration er
        JOIN jogger j ON er.JoggerEmail = j.Email
        WHERE er.EventID = %s
        """
        return BaseRepository.execute_query(query, (event_id,))

    @staticmethod
    def get_registered_events_for_jogger(jogger_email):
        """Get all events a jogger is registered for."""
        query = """
        SELECT je.*, er.TimeStamp as RegistrationTime
        FROM eventregistration er
        JOIN joggingevent je ON er.EventID = je.EventID
        WHERE er.JoggerEmail = %s
        ORDER BY je.EventDate
        """
        return BaseRepository.execute_query(query, (jogger_email,))

    @staticmethod
    def check_registration(event_id, jogger_email):
        """Check if a jogger is registered for an event."""
        query = (
            "SELECT * FROM eventregistration WHERE EventID = %s AND JoggerEmail = %s"
        )
        result = BaseRepository.execute_query(query, (event_id, jogger_email))
        return bool(result)

    @staticmethod
    def count_registrations(event_id):
        """Count the number of registrations for an event."""
        query = "SELECT COUNT(*) as count FROM eventregistration WHERE EventID = %s"
        result = BaseRepository.execute_query(query, (event_id,))
        return result[0]["count"] if result else 0

    @staticmethod
    def get_registration(event_id, jogger_email):
        """Get registration details for a specific event and jogger."""
        query = """
        SELECT er.*, je.EventName
        FROM eventregistration er
        JOIN joggingevent je ON er.EventID = je.EventID
        WHERE er.EventID = %s AND er.JoggerEmail = %s
        """
        result = BaseRepository.execute_query(query, (event_id, jogger_email))
        return result[0] if result else None


class JoggingSessionRepository(BaseRepository):
    """Repository for jogging session operations."""

    @staticmethod
    def get_sessions_for_jogger(jogger_email):
        """Get all jogging sessions for a jogger."""
        query = """
        SELECT j.*, jr.RouteName 
        FROM jogging j
        LEFT JOIN joggingroute jr ON j.RouteID = jr.RouteID
        WHERE j.JoggerEmail = %s
        ORDER BY j.StartDT DESC
        """
        return BaseRepository.execute_query(query, (jogger_email,))

    @staticmethod
    def get_session_by_id(session_id):
        """Get a jogging session by ID."""
        query = """
        SELECT j.*, jr.RouteName 
        FROM jogging j
        LEFT JOIN joggingroute jr ON j.RouteID = jr.RouteID
        WHERE j.SessionID = %s
        """
        result = BaseRepository.execute_query(query, (session_id,))
        return result[0] if result else None

    @staticmethod
    def create_session(start_dt, end_dt, distance, jogger_email, route_id=None):
        """Create a new jogging session."""
        query = """
        INSERT INTO jogging (StartDT, EndDT, Distance, JoggerEmail, RouteID) 
        VALUES (%s, %s, %s, %s, %s)
        """
        return BaseRepository.execute_query(
            query, (start_dt, end_dt, distance, jogger_email, route_id), commit=True
        )["id"]

    @staticmethod
    def update_session(session_id, start_dt, end_dt, distance, route_id=None):
        """Update a jogging session."""
        query = """
        UPDATE jogging 
        SET StartDT = %s, EndDT = %s, Distance = %s, RouteID = %s 
        WHERE SessionID = %s
        """
        BaseRepository.execute_query(
            query, (start_dt, end_dt, distance, route_id, session_id), commit=True
        )

    @staticmethod
    def delete_session(session_id):
        """Delete a jogging session."""
        query = "DELETE FROM jogging WHERE SessionID = %s"
        BaseRepository.execute_query(query, (session_id,), commit=True)

    @staticmethod
    def add_session_to_event(event_id, session_id):
        """Associate a session with an event."""
        query = "INSERT INTO EventSession (EventID, SessionID) VALUES (%s, %s)"
        BaseRepository.execute_query(query, (event_id, session_id), commit=True)

    @staticmethod
    def remove_session_from_event(event_id, session_id):
        """Remove a session from an event."""
        query = "DELETE FROM EventSession WHERE EventID = %s AND SessionID = %s"
        BaseRepository.execute_query(query, (event_id, session_id), commit=True)


class ReviewRepository(BaseRepository):
    """Repository for review operations."""

    @staticmethod
    def get_route_reviews(route_id):
        """Get all reviews for a route."""
        query = """
        SELECT rr.*, j.Name as JoggerName
        FROM routereview rr
        JOIN jogger j ON rr.JoggerEmail = j.Email
        WHERE rr.RouteID = %s
        ORDER BY rr.ReviewID DESC
        """
        return BaseRepository.execute_query(query, (route_id,))

    @staticmethod
    def get_event_reviews(event_id):
        """Get all reviews for an event."""
        query = """
        SELECT er.*, j.Name as JoggerName
        FROM eventreview er
        JOIN jogger j ON er.JoggerEmail = j.Email
        WHERE er.EventID = %s
        ORDER BY er.ReviewID DESC
        """
        return BaseRepository.execute_query(query, (event_id,))

    @staticmethod
    def get_route_review_by_jogger(route_id, jogger_email):
        """Get a route review by a specific jogger."""
        query = "SELECT * FROM routereview WHERE RouteID = %s AND JoggerEmail = %s"
        result = BaseRepository.execute_query(query, (route_id, jogger_email))
        return result[0] if result else None

    @staticmethod
    def get_event_review_by_jogger(event_id, jogger_email):
        """Get an event review by a specific jogger."""
        query = "SELECT * FROM eventreview WHERE EventID = %s AND JoggerEmail = %s"
        result = BaseRepository.execute_query(query, (event_id, jogger_email))
        return result[0] if result else None

    @staticmethod
    def create_route_review(route_id, jogger_email, rating, comment=None):
        """Create a new route review."""
        query = "INSERT INTO routereview (RouteID, JoggerEmail, Rating, Comment) VALUES (%s, %s, %s, %s)"
        BaseRepository.execute_query(
            query, (route_id, jogger_email, rating, comment), commit=True
        )

    @staticmethod
    def create_event_review(event_id, jogger_email, rating, comment=None):
        """Create a new event review."""
        query = "INSERT INTO eventreview (EventID, JoggerEmail, Rating, Comment) VALUES (%s, %s, %s, %s)"
        BaseRepository.execute_query(
            query, (event_id, jogger_email, rating, comment), commit=True
        )

    @staticmethod
    def update_route_review(review_id, rating, comment=None):
        """Update a route review."""
        query = "UPDATE routereview SET Rating = %s, Comment = %s WHERE ReviewID = %s"
        BaseRepository.execute_query(query, (rating, comment, review_id), commit=True)

    @staticmethod
    def update_event_review(review_id, rating, comment=None):
        """Update an event review."""
        query = "UPDATE eventreview SET Rating = %s, Comment = %s WHERE ReviewID = %s"
        BaseRepository.execute_query(query, (rating, comment, review_id), commit=True)

    @staticmethod
    def delete_route_review(review_id):
        """Delete a route review."""
        query = "DELETE FROM routereview WHERE ReviewID = %s"
        BaseRepository.execute_query(query, (review_id,), commit=True)

    @staticmethod
    def delete_event_review(review_id):
        """Delete an event review."""
        query = "DELETE FROM eventreview WHERE ReviewID = %s"
        BaseRepository.execute_query(query, (review_id,), commit=True)

    @staticmethod
    def get_route_average_rating(route_id):
        """Get the average rating for a route."""
        query = """
        SELECT AVG(Rating) as average_rating, COUNT(*) as review_count
        FROM routereview 
        WHERE RouteID = %s
        """
        result = BaseRepository.execute_query(query, (route_id,))
        return {
            "average": (
                round(result[0]["average_rating"], 1)
                if result[0]["average_rating"]
                else 0
            ),
            "count": result[0]["review_count"],
        }

    @staticmethod
    def get_event_average_rating(event_id):
        """Get the average rating for an event."""
        query = """
        SELECT AVG(Rating) as average_rating, COUNT(*) as review_count
        FROM eventreview 
        WHERE EventID = %s
        """
        result = BaseRepository.execute_query(query, (event_id,))
        return {
            "average": (
                round(result[0]["average_rating"], 1)
                if result[0]["average_rating"]
                else 0
            ),
            "count": result[0]["review_count"],
        }


class LeaderboardRepository(BaseRepository):
    """Repository for leaderboard operations."""

    @staticmethod
    def get_leaderboard_for_event(event_id):
        """Get the leaderboard for an event."""
        query = "SELECT * FROM leaderboard WHERE EventID = %s ORDER BY `Rank`"
        return BaseRepository.execute_query(query, (event_id,))
