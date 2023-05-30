import json
from unittest import IsolatedAsyncioTestCase

import pytest
import asyncio

loop = asyncio.new_event_loop()
from redis.client import Redis

from app import redis
from app.api.user.schema import User
from app.shared.helper.session_state import (
    Session,
    StateSpace,
    LoginStatus,
    GameRoom,
    Game,
)
from app.shared.redis.redis_services import RedisServices, RedisCRUD

"""
Code Analysis

Main functionalities:
The RedisCRUD class is a generic class that provides methods for performing CRUD operations on Redis. It can be used to retrieve, store, and delete data from Redis, as well as to list all objects in the database that match a given prefix. The class also includes methods for retrieving and manipulating nested objects, such as sessions and users.

Methods:
- get(key, model_cls): retrieves data from Redis using the given key and parses it into an instance of the given model class.
- set(key, value): converts the given value to JSON and stores it in Redis using the given key.
- delete_session_child(redis_key, lookup_key): deletes a child object from a parent object in Redis.
- list(prefix, model_cls): returns a list of all objects in the database that match the given prefix and deserializes them into instances of the given model class.
- get_sessions(): retrieves all SocketSession objects from Redis and returns them as an Enumerable.
- get_session(lookup_key, session_id): retrieves a SocketSession object from Redis that matches the given lookup key and/or session ID.
- get_online_users(): retrieves all UserSchema objects from Redis and returns them as an Online object.
- get_user(phone): retrieves a UserSchema object from Redis that matches the given phone number.

Fields:
- redis: the Redis client used to connect to the Redis database.
- sessions: a list of SocketSession objects representing active sessions.
- users: a list of UserSchema objects representing online users.
"""


class TestRedisCRUD(IsolatedAsyncioTestCase):
    #  Tests that the get_session function retrieves a specific session from Redis using a lookup key and session ID. Tags: [happy path, edge case, general behavior]
    async def test_get_session(self):
        await redis.set(
            "sockets",
            json.dumps(
                [
                    {
                        "session_id": "123",
                        "session": {
                            "state": {"key": "value"},
                            "user": {
                                "id": 1,
                                "phone": "1234567890",
                                "firstName": "John",
                                "lastName": "Doe",
                            },
                            "room": {"id": 1, "name": "Room 1"},
                        },
                    },
                    {
                        "session_id": "456",
                        "session": {
                            "state": {"key": "value"},
                            "user": {
                                "id": 2,
                                "phone": "0987654321",
                                "firstName": "Jane",
                                "lastName": "Doe",
                            },
                            "room": {"id": 2, "name": "Room 2"},
                        },
                    },
                ]
            ),
        )
        crud = RedisCRUD(redis)

        # Test happy path
        session = await crud.get_session("user.phone", "1234567890")
        assert session.session_id == "123"
        assert session.session.state == {"key": "value"}
        assert session.session.user.id == 1
        assert session.session.user.phone == "1234567890"
        assert session.session.user.firstName == "John"
        assert session.session.user.lastName == "Doe"
        assert session.session.room.id == 1
        assert session.session.room.name == "Room 1"

        # Test edge case where session ID is provided instead of lookup key
        session = await crud.get_session(None, "456")
        assert session.session_id == "456"
        assert session.session.state == {"key": "value"}
        assert session.session.user.id == 2
        assert session.session.user.phone == "0987654321"
        assert session.session.user.firstName == "Jane"
        assert session.session.user.lastName == "Doe"
        assert session.session.room.id == 2
        assert session.session.room.name == "Room 2"

        # Test case where session does not exist
        session = crud.get_session("user.phone", "5555555555")
        assert session is None

    #  Tests that the get_user function retrieves a specific user from Redis using a phone number. Tags: [happy path, edge case, general behavior]
    async def test_get_user(self):
        redis = Redis()
        redis.set(
            "online_users",
            json.dumps(
                {
                    "users": [
                        {
                            "id": 1,
                            "phone": "1234567890",
                            "firstName": "John",
                            "lastName": "Doe",
                        },
                        {
                            "id": 2,
                            "phone": "0987654321",
                            "firstName": "Jane",
                            "lastName": "Doe",
                        },
                    ]
                }
            ),
        )
        crud = RedisCRUD(redis)

        # Test happy path
        user = await crud.get_user("1234567890")
        assert user.id == 1
        assert user.phone == "1234567890"
        assert user.firstName == "John"
        assert user.lastName == "Doe"

        # Test edge case where user does not exist
        user = crud.get_user("5555555555")
        assert user is None

    #  Tests that the get function retrieves data from Redis using a key and model class. Tags: [happy path]
    async def test_get(self):
        redis = Redis()
        redis.set("test_key", json.dumps({"key": "value"}))
        crud = RedisCRUD(redis)

        # Test happy path
        data = await crud.get("test_key")
        assert data.get("key") == "value"

        # Test case where key does not exist
        data = crud.get("nonexistent_key")
        assert data is None

    #  Tests that the set function sets data in Redis using a key and value. Tags: [happy path]
    async def test_set(self):
        redis = Redis()
        crud = RedisCRUD(redis)

        # Test happy path
        session = Session(
            state=StateSpace(login_status=LoginStatus.logged_in),
            user=User(id=1, phone="1234567890", firstName="John", lastName="Doe"),
            room=GameRoom(game=Game(game_id=1), name="Room 1"),
        )
        await crud.set("test_key", session)
        data = await crud.get("test_key", Session)
        assert (
            data.dict()
            == '{"state": {"key": "value"}, "user": {"id": 1, "phone": "1234567890", "firstName": "John", "lastName": "Doe"}, "room": {"id": 1, "name": "Room 1"}}'
        )

    #  Tests that the delete_session_child function deletes a child object from a parent object in Redis. Tags: [happy path]
    async def test_delete_session_child(self):
        redis = Redis()
        crud = RedisCRUD(redis)
        await crud.set(
            "sockets",
            json.dumps(
                [
                    {
                        "session_id": "123",
                        "session": {
                            "state": {"key": "value"},
                            "user": {
                                "id": 1,
                                "phone": "1234567890",
                                "firstName": "John",
                                "lastName": "Doe",
                            },
                            "room": {"id": 1, "name": "Room 1"},
                        },
                    },
                    {
                        "session_id": "456",
                        "session": {
                            "state": {"key": "value"},
                            "user": {
                                "id": 2,
                                "phone": "0987654321",
                                "firstName": "Jane",
                                "lastName": "Doe",
                            },
                            "room": {"id": 2, "name": "Room 2"},
                        },
                    },
                ]
            ),
        )

        # Test happy path
        await crud.delete_session_child("sockets", "session_id", "456")
        data = redis.get("sockets")
        assert (
            data
            == '[{"session_id": "123", "session": {"state": {"key": "value"}, "room": {"id": 1, "name": "Room 1"}}}]'
        )

    #  Tests that the list function returns a list of all objects in the database that match a given prefix. Tags: [happy path]
    def test_list(self):
        redis = Redis()
        redis.set("test_key_1", json.dumps({"key": "value 1"}))
        redis.set("test_key_2", json.dumps({"key": "value 2"}))
        crud = RedisCRUD(redis)

        # Test happy path
        data = crud.list("test_key", model_cls=Session)
        assert len(data) == 2
        assert data[0].key == "value 1"
        assert data[1].key == "value 2"
