"""SendMessage."""
import json
from dataclasses import dataclass

import requests
from requests.exceptions import HTTPError
from flask import current_app


# Example:
"""
curl -XPOST http://localhost:8545 -H 'Content-type: application/json' \
    '{
     "jsonrpc": "2.0",
     "method": "wakuext_setDisplayName",
     "params": [
         "[HOT_DISPLAY_NAME]"
     ],
     "id": 1
     }'
"""


@dataclass
class SetDisplayName:
    """Sets the display name of the target waku node, in case it will be sending messages to people."""

    display_name: str

    def execute(self, config, task_data):
        url = f'{current_app.config["CONNECTOR_PROXY_WAKU_BASE_URL"]}'
        headers = {"Accept": "application/json", "Content-type": "application/json"}
        request_body = {
            "jsonrpc": "2.0",
            "method": "wakuext_setDisplayName",
            "params": [self.display_name],
            "id": 1,
        }

        response = {}
        status_code = None
        try:
            raw_response = requests.post(url, json.dumps(request_body), headers=headers)
            raw_response.raise_for_status()
            status_code = raw_response.status_code
            parsed_response = json.loads(raw_response.text)
            response = parsed_response
        except HTTPError as ex:
            status_code = ex.response.status_code
            response['error'] = str(ex)
        except Exception as ex:
            response['error'] = str(ex)
            status_code = 500

        return ({
            "response": json.dumps(response),
            "status": status_code,
            "mimetype": "application/json",
        })
