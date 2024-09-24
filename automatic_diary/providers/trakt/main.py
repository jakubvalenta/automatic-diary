import json
import logging
import os
from pathlib import Path
from typing import Iterator

from trakt import Trakt

from automatic_diary.model import Item

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name


class Application(object):
    def __init__(self, config):
        self.authorization = None
        self.token_name = "token.json"

        # Bind trakt events
        Trakt.on("oauth.token_refreshed", self.on_token_refreshed)

        # Configure client
        Trakt.configuration.defaults.app(
            id=config[
                "app_id"
            ]  # (e.g. "478" for https://trakt.tv/oauth/applications/478)
        )

        Trakt.configuration.defaults.client(
            id=config["key_id"], secret=config["key_secret"]
        )

    def auth(self) -> bool:
        if os.path.exists(self.token_name):
            with open(self.token_name, "r") as f:
                self.authorization = json.load(f)
                return True

        # Request authentication
        print("Navigate to %s" % Trakt["oauth/pin"].url())
        pin = input("Pin: ")

        # Exchange `pin` for an account authorization token
        self.authorization = Trakt["oauth"].token_exchange(
            pin, "urn:ietf:wg:oauth:2.0:oob"
        )

        if not self.authorization:
            logger.warn("ERROR: Authentication failed")
            return False

        logger.info("Token exchanged - authorization: %r" % self.authorization)
        self.save_token()
        return True

    def on_token_refreshed(self, response):
        # OAuth token refreshed, save token for future calls
        self.authorization = response
        logger.info("Token refreshed - authorization: %r" % self.authorization)
        self.save_token()

    def save_token(self):
        logger.info("Saving Token to disk")
        with open(self.token_name, "w") as f:
            json.dump(self.authorization, f)

    def movies(self) -> Iterator:
        logger.info("Reading movies")
        with Trakt.configuration.oauth.from_response(self.authorization):
            return Trakt["sync/history"].movies(pagination=True)

    def shows(self):
        logger.info("Reading shows")
        with Trakt.configuration.oauth.from_response(self.authorization):
            return Trakt["sync/history"].shows(pagination=True)


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    app = Application(config)
    app.auth()

    for m in app.movies():
        yield Item.normalized(
            datetime_=m.watched_at,
            text=m.title,
            provider=provider,
            subprovider="movies",
        )

    for s in app.shows():
        yield Item.normalized(
            datetime_=s.watched_at,
            text='"' + s.show.title + '" : ' + s.title,
            provider=provider,
            subprovider="shows",
        )
