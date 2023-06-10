"""
@author: Kuro
@github: slapglif
"""
from datetime import datetime
from typing import Optional

import pytz

from app import logging
from app.api.user.models import User
from app.rpc.game.schema import Session, Socket, Room, BaseUser

logger = logging.getLogger(__name__)


class SocketServer(Socket):
    """
    The SocketServer class is a class that represents a socket server.
    """

    _socket = None

    def __new__(cls, namespace: str = "/") -> "SocketServer":
        if cls._socket is None:
            cls._socket: SocketServer = super().__new__(SocketServer)
        return cls._socket

    @classmethod
    def create_socket(cls, namespace: str = "/") -> "SocketServer":
        """
        Creates a socket instance and returns it.

        :return: A socket instance.
        :rtype: AsyncNamespace
        """
        _socket = super().__new__(cls)
        _socket.save()
        return _socket

    def create_session(self, session_id: str, user: User = None) -> Session:
        """
        Creates a session for the given user and returns it.

        :param user:The user to create a session for.
        :param session_id: The session id to use for the session.
        :return: A session instance.
        :rtype: Session
        """
        session = Session(id=session_id, socket_id=self.pk)
        session.save()
        self.sessions.append(session)
        self.save()
        logger.info(f"create_session: {session}")

        if user:
            user = BaseUser.from_orm(user)
            return self.add_user_to_session(user, session)

        # logger.info(f"create_session_user: {user}")
        # # user = self.query(self.sessions).where(filter_arg=lambda _user: _user.id == user.id).first()
        # return self.add_user_to_session(user, session)
        return session

    def add_user_to_session(self, user: BaseUser, session: Session) -> Session:
        user.save()
        session.user = user
        session.save()
        logger.info(f"create_session_got_user: {user}")
        return session

    @classmethod
    def sync_session_user(cls, session: Session) -> Optional[BaseUser]:
        """
        The sync_session_user function is used to sync the user object in a session with the database.
            This function is called when a user logs in, and also when they log out.
            It's purpose is to ensure that any changes made by other users are reflected on this client.

        Args:
            session: Session: Get the user id from the session

        Returns:
            True if the user was successfully synced
        """

        user = session.user and User.get(id=session.user.id).first()
        session_user = BaseUser.from_orm(user)
        logger.info(f"synced session_user: {session_user}")
        session_user.save()
        return session_user

    @classmethod
    def sync_db_user(cls, session: Session) -> Optional[User]:
        """
        The sync_db_user function is used to sync the user data from the session with
        the database. This function is called in a few places, but most importantly it's
        called when a user logs out of their account. When this happens, we want to make sure that any changes made by the
        user are saved into our database so that they can be accessed again later on.

        Args:
            session: Session: Get the user's session

        Returns:
            None if the user is not found in the database
        """

        user = User.get(id=session.user.id).first()
        if not user:
            return
        session_user = session.user
        user.update(
            **session_user.dict(
                exclude={"pk", "room"}, exclude_none=True, exclude_unset=True
            )
        )
        user.save()
        logger.info(f"synced db_user: {user}")
        return user

    def save_session_state(self, session):
        session.state.save()
        session.save()
        self.save()

    def redis_logout(
        self, session: Session, emit_message: str = None
    ) -> Optional[bool]:
        """
        Logs out the user with the given user ID by setting their authToken to None, marking them as offline, and updating their
        session in Redis. Returns True if the logout was successful, False otherwise.

        :param emit_message:
        :param session: The session to logout.
        :rtype: bool
        """

        self.sync_session_user(session)
        self.sync_db_user(session)
        # emit_message = emit_message or f'{"socket": session.id, "data": session.user}'
        session.user.delete(pk=session.user.pk)
        self.sessions.remove(session)
        session.delete(pk=session.pk)
        session.save()
        logger.info(f"logout: User {session.user} session deleted in redis")
        return True

    def redis_login(
        self, session_id: str, auth_token: str = None, emit_message: str = None
    ) -> Optional[Session]:
        """
        The redis_login function is used to log a user into the application.
            It takes in an auth_token as a parameter, and returns either True or False depending on whether or not the login was successful.
            The function first checks if there is already an active session for that user by checking if their auth_token exists in the BaseUser table of our database.
            If it does exist, then we know that they are already logged in and we return False to indicate this fact.  Otherwise, we create a new session for them using their auth_token as well as creating a room for them based on their username (which will be explained

        Args:
            auth_token: str: Pass the auth_token to the function

        Returns:
            :param session_id:
            :param auth_token:
            :param emit_message:

        """
        user = User.get(auth_token=auth_token).first()
        if (
            session := self.sessions
            and self.query(self.sessions)
            .where(
                filter_arg=lambda _session: _session.user
                and _session.user.auth_token == auth_token
            )
            .first_or_default()
        ):
            # self.redis_logout(session)
            logger.info("login: User already logged in")
            return session
        if not user:
            logger.info("no db user found, have an agent create the user")
            return
        session = self.create_session(session_id, user=user)
        self.change_room(session)
        self.sync_db_user(session)
        # emit_message = emit_message or f'{"socket": socket.id, "data": user}'
        logger.info(f"login: User {session.user} session created in redis")
        return session

    def create_room(self, new_room: str):
        """
        The create_room function is used to create a new room in the database.
            It takes in a room name as a parameter, and returns either True or False depending on whether or not the room was successfully created.

        Args:
            new_room: str: Pass the new room name to the function

        Returns:
            A room object
        """
        room = Room(name=new_room, created_at=str(datetime.now(pytz.utc)))
        room.save()
        self.rooms.append(room)
        self.save()
        return room

    def change_room(self, session: Session, new_room: str = None) -> Optional[Room]:
        """
        The change_room function is used to create a room if it doesn't exist, and add the user to that room.
        If the user is already in that room, then they are logged out of their current session.

        Args:
            session: Get the user's session

            Returns:
                A room object
        """
        if not session.user or not session.user.room:
            return self.set_default_room(session)
        if session.user.room.name == new_room:
            return

        room = (
            self.rooms
            and self.query(self.rooms).where(name=new_room).first()
            or self.create_room(new_room)
        )
        room.name not in [x.name for x in self.rooms] and self.rooms.append(room)
        self.save()
        session.user.room = room
        session.save()
        return room

    def set_default_room(self, session):
        """
        The set_default_room function is called when a new session is created.
        It creates a default room for the session, and sets that as the current room for all users in the session.

        Args:
            self: Refer to the object itself
            session: Set the room for that session

        Returns:
            The room object

        """
        room = self.rooms and self.query(self.rooms).where(name="lobby").first()
        if not room:
            room = self.create_room("lobby")
            self.rooms.append(room)

        session.user.room = room
        session.save()
        self.save()
        return room

    def enter_room(self, session_id):
        session = (
            self.sessions and self.query(self.sessions).where(id=session_id).first()
        )
        self.change_room(session)
        session.save()
        self.save()
        return session
