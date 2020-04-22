import logging

log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)
import connexion
from flask_testing import TestCase

import json


class BaseTestCase(TestCase):
    def create_app(self):
        logging.getLogger("connexion.operation").setLevel("ERROR")
        app = connexion.App(__name__, specification_dir="./")
        app.add_api("openapi.yaml")

        return app.app


class TestPublicController(BaseTestCase):
    """PublicController integration test stubs"""

    def test_a(self):
        """Test case for get_echo
        Ritorna un timestamp in formato RFC5424.
        """
        for u in ("harry", "draco"):
            response = self.client.open(f"/user/{u}", method="POST")
            self.assert200(
                response, "Response body is : " + response.data.decode("utf-8")
            )
            response = self.client.open(f"/user/{u}", method="GET")
            self.assert200(
                response, "Response body is : " + response.data.decode("utf-8")
            )

    def test_cast_spell(self):
        response = self.client.open("/restart", method="POST")
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))
        spells = response.json["status"]["spells"]

        for s in spells:
            data = json.dumps({"s": s}).encode()
            response = self.client.open(
                "/cast/harry/draco",
                method="POST",
                data=data,
                headers={"content-type": "application/json"},
            )
            self.assert200(
                response, "Response body is : " + response.data.decode("utf-8")
            )
            log.info(response.json)
            response = self.client.open(
                "/cast/draco/harry",
                method="POST",
                data=data,
                headers={"content-type": "application/json"},
            )
            self.assert200(
                response, "Response body is : " + response.data.decode("utf-8")
            )
            log.info(response.json)
