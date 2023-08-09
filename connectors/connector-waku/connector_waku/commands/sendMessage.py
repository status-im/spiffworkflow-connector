"""SendMessage."""
import json
from dataclasses import dataclass
from typing import Optional, Tuple

import requests
from requests.exceptions import HTTPError
from flask import current_app


# Example:
"""
curl -XPOST http://localhost:8545 -H 'Content-type: application/json' \
    '{
     "jsonrpc": "2.0",
     "method": "wakuext_sendOneToOneMessage",
     "params": [
         {
         "id": "0xPUBLIC_KEY",
         "message": "hello there, try http://167.172.242.138:7001/"
         }
     ],
     "id": 1
     }'
"""


@dataclass
class SendMessage:
    """SendMessage."""

    message: str
    message_type: str
    recipient: list[str]

    def send_message(
        self, message_type_to_use: str, rec: str, message_to_send: Optional[str] = None, params: Optional[list] = None
    ) -> Tuple[dict, int, bool]:
        url = f'{current_app.config["CONNECTOR_PROXY_WAKU_BASE_URL"]}'
        headers = {"Accept": "application/json", "Content-type": "application/json"}
        if params is None:
            params = [{"id": rec, "message": message_to_send}]
        request_body = {
            "jsonrpc": "2.0",
            "method": message_type_to_use,
            "params": params,
            "id": 1,
        }

        response = {}
        status_code = None
        successful = False
        try:
            raw_response = requests.post(url, json.dumps(request_body), headers=headers)
            raw_response.raise_for_status()
            status_code = raw_response.status_code
            parsed_response = json.loads(raw_response.text)
            response = parsed_response
            if not self.response_has_error(response) and status_code == 200:
                successful = True
        except HTTPError as ex:
            status_code = ex.response.status_code
            response['error'] = str(ex)
        except Exception as ex:
            response['error'] = str(ex)
            status_code = 500
        return (response, status_code, successful)

    def response_has_error(self, response: dict) -> bool:
        if 'error' in response:
            return True
        if 'result' in response:
            return response['result'] == "0x0400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
        return False

    def execute(self, _config, _task_data):
        """Execute."""
        responses = []
        all_calls_returned_200 = True
        for rec in self.recipient:
            if not isinstance(rec, str):
                continue
            
            # we also tried wakuext_sendContactRequest before wakuext_addContact.
            # wakuext_sendContactRequest also took a third parameter after the rec parameter for the message that would appear
            # alongside the contact request. But the message also appeared in your messages foreever and ever, which was not
            # very compatible with sending a contact request with every message. Now, if you are not already a contact, you get
            # a prompt to approve the request, and then you get all of the messages from the "spiff" user.
            receiver_name = rec
            status_code = None
            response = None
            successful = False

            ens_lookup_failed = False
            if receiver_name.endswith('.eth'):
                response, status_code, successful = self.send_message('ens_publicKeyOf', receiver_name, params=[1, receiver_name])
                if successful:
                    receiver_name = response['result']
                else:
                    all_calls_returned_200 = False
                    ens_lookup_failed = True

            if not ens_lookup_failed:
                response, status_code, successful = self.send_message('wakuext_addContact', receiver_name)
                if successful:
                    response, status_code, successful = self.send_message(self.message_type, receiver_name, self.message)
                else:
                    all_calls_returned_200 = False

            responses.append({
                "response": response,
                "successful": successful,
                "status": status_code,
            })
        return ({
            "response": json.dumps(responses),
            "node_returned_200": all_calls_returned_200,
            "status": 200,
            "mimetype": "application/json",
        })
