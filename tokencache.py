#!/usr/bin/python
"""Simple module for file based cache of OAuth token."""
from json import dump, load, loads
from time import time
from requests import post
from settings import CLIENT_ID, CLIENT_SECRET

CACHE_FILE = "/var/tmp/wcloauth.json"


def gettoken() -> str:
    """Return OAuth token."""
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as infile:
            response_data = load(infile)
        if int(time()) > response_data["expires_at"]:
            raise TimeoutError
    except (TimeoutError, FileNotFoundError):
        url = "https://www.warcraftlogs.com/oauth/token"

        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
        }

        response = post(url, data=data, timeout=30)

        response_data = loads(response.text)
        response_data["expires_at"] = int(time()) + int(response_data["expires_in"])

        with open(CACHE_FILE, "w", encoding="utf-8") as outfile:
            dump(response_data, outfile)
    finally:
        token = response_data["access_token"]

    return f"Bearer {token}"
