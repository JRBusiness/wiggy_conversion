import json
import time
from base64 import b64decode
from datetime import datetime
from typing import Optional, List, Dict, Any

import pytz
from loguru import logger
from redis_om import JsonModel, Field
from bs4 import BeautifulSoup
import requests
import redis


class EmailMessage(JsonModel):
    id: str
    body_mime: str

    # add any other relevant fields here
    class Meta:
        indexes = ['id']


domain = "mail.baohule.com"
api_key = "f4c2130e7365dce72a71b11e543b5cfb-7764770b-41949093"
inbox_url = f"https://api.mailgun.net/v3/{domain}/messages/"
headers = {"Accept": "message/rfc2822", "Authorization": f"Basic {api_key}"}
params = {
    "limit": "10",  # only fetch 10 latest messages at a time
}

session = requests.Session()
session.headers.update({"Accept": "message/rfc2822"})
session.params = dict({"limit": "10"})


def get_logs():
    return session.get(
        inbox_url,
        # "https://api.mailgun.net/v3/mail.baohule.com/events",
        headers=headers,
        auth=("api", api_key),
        params={
            "begin": "Fri, 3 May 2013 09:00:00 -0000",
            "ascending": "yes",
            "limit": 25,
            "pretty": "yes",
            "recipient": "joe@example.com",
        },
    )


r = get_logs()


class Pages(JsonModel):
    next: Optional[str]
    previous: Optional[str]


class EventResponse(JsonModel):
    items: list
    paging: Pages


#

class Email(JsonModel):
    code: str
    timestamp = Field(index=True, default=lambda: datetime.now(pytz.utc))


def parse_email(email: str) -> Email:
    # decode base64 email
    # decoded_email = b64decode(email_base64).decode()

    # parse HTML with BeautifulSoup
    soup = BeautifulSoup(email, "html.parser")

    # find the code in <b> tag
    code = soup.find('b').text

    return Email(code=code)




#
# class Envelope(JsonModel):
#     sender: str
#     transport: str
#     targets: str
#
#
# class DeliveryStatus(JsonModel):
#     attempt_no: int = Field(..., alias='attempt-no')
#     code: int
#     session_seconds: float = Field(..., alias='session-seconds')
#     message: str
#     description: str
#
#
# class Headers(JsonModel):
#     message_id: str = Field(..., alias='message-id')
#     to: str
#     subject: str
#     from_: str = Field(..., alias='from')
#
#
# class Message(JsonModel):
#     attachments: List
#     size: int
#     headers: Headers
#
#
# class Flags(JsonModel):
#     is_authenticated: bool = Field(default=None, alias='is-authenticated')
#     is_test_mode: bool = Field(default=None, alias='is-test-mode')
#     is_system_test: bool = Field(default=None, alias='is-system-test')
#     is_routed: bool = Field(default=None, alias='is-routed')
#
#
# class Storage(JsonModel):
#     region: Optional[str] = Field(default=None)
#     env: Optional[str] = Field(default=None)
#     lookup_key: Optional[str] = Field(default=None, alias='key')
#     url: Optional[str] = Field(default=None)
#
#
# # class WebhookData(JsonModel):
# #     envelope: Envelope
# #     campaigns: Optional[None]
# #     id: str
# #     recipient: str
# #     recipient_domain: str = Field(..., alias='recipient-domain')
# #     log_level: str = Field(..., alias='log-level')
# #     user_variables: Dict[str, Any] = Field(default=None, alias='user-variables')
# #     tags: List
# #     delivery_status: DeliveryStatus = Field(..., alias='delivery-status')
# #     timestamp: float
# #     message: Message
# #     event: str
# #     flags: Flags
# #     storage: Storage
#
#
# """
# {"event-data":{"event":"delivered","flags":{"is-authenticated":false,"is-big":false,"is-routed":true,"is-system-test":false,"is-test-mode":false},"id":"0eZPCuc_RbCrFyY_Vl71Ew","log-level":"info","message":{"attachments":[],"headers":{"from":"security@locateplus.com","message-id":"MW2PR13MB41877D4DA6C6D040F4BE22B9DC4FA@MW2PR13MB4187.namprd13.prod.outlook.com","subject":"LocatePlus Security Token","to":"junyongwang76@gmail.com"},"size":16270},"recipient":"mike.b.developer@gmail.com","recipient-domain":"gmail.com","storage":{"key":"BAABAAXEspiXLbA_H_5GOJtOhBSUNFXvZA==","url":"https://storage-us-east4.api.mailgun.net/v3/domains/mail.baohule.com/messages/BAABAAXEspiXLbA_H_5GOJtOhBSUNFXvZA=="},"tags":[],"timestamp":1685769818.9247808},"signature":{"signature":"e950bd4b9e1bf81bd2dd16c97edf77db29afa93ec72677affcab1fed184564e0","timestamp":"1685769818","token":"3658071b6ecc3242dc49d93a5acffb8eed7f19796f61c47198"}}
#
# """
#
#
# class EmailModelOld(JsonModel):
#     content_type: Optional[str] = Field(alias='Content-Type')
#     date: Optional[str] = Field(alias='Date')
#     dkim_signature: Optional[str] = Field(alias='Dkim-Signature')
#     from_: Optional[str] = Field(alias='From')
#     message_id: Optional[str] = Field(alias='Message-Id')
#     mime_version: Optional[str] = Field(alias='Mime-Version')
#     received: Optional[str] = Field(alias='Received')
#     subject: Optional[str] = Field(alias='Subject')
#     to: Optional[str] = Field(alias='To')
#     x_envelope_from: Optional[str] = Field(alias='X-Envelope-From')
#     x_gm_message_state: Optional[str] = Field(alias='X-Gm-Message-State')
#     x_google_dkim_signature: Optional[str] = Field(alias='X-Google-Dkim-Signature')
#     x_google_smtp_source: Optional[str] = Field(alias='X-Google-Smtp-Source')
#     x_mailgun_incoming: Optional[str] = Field(alias='X-Mailgun-Incoming')
#     x_received: Optional[str] = Field(alias='X-Received')
#     sender: Optional[str] = Field(alias='sender')
#     recipients: Optional[str] = Field(alias='recipients')
#     body_mime: Optional[str] = Field(alias='body-mime')
#
#
# class Flags(JsonModel):
#     is_authenticated: bool = Field(..., alias='is-authenticated')
#     is_big: bool = Field(..., alias='is-big')
#     is_routed: bool = Field(..., alias='is-routed')
#     is_system_test: bool = Field(..., alias='is-system-test')
#     is_test_mode: bool = Field(..., alias='is-test-mode')
#
#
#
#
# class EventData(JsonModel):
#     event: Optional[str]
#     flags: Optional[Flags]
#     id: Optional[str]
#     log_level: Optional[str] = Field(..., alias='log-level')
#     message: Optional[Message]
#     recipient: Optional[str]
#     recipient_domain: Optional[str] = Field(..., alias='recipient-domain')
#     storage: Optional[Storage]
#     tags: Optional[List]
#     timestamp: Optional[float]
#
#
# class Signature(JsonModel):
#     signature: Optional[str]
#     timestamp: Optional[str]
#     token: Optional[str]
#
#
# class SignatureModel(JsonModel):
#     event_data: Optional[EventData] = Field(None, alias='event-data')
#     signature: Optional[Signature] = None
