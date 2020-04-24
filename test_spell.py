import logging

from app import DataclassJSONEncoder, _misspelt, SPELL_KO, SPELL_OK, SPELL_MISSING

log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)
import connexion
from flask_testing import TestCase

import json


class BaseTestCase(TestCase):
    def create_app(self):
        logging.getLogger("connexion.operation").setLevel("ERROR")
        app = connexion.App(__name__, specification_dir="./")
        app.app.json_encoder = DataclassJSONEncoder
        app.add_api("openapi.yaml")

        return app.app

    def get(self, url):
        return self.client.open(url)

    def post(self, url, data=None):
        return self.client.open(
            url, method="POST", data=data, headers={"content-type": "application/json"},
        )


class TestPublicController(BaseTestCase):
    """PublicController integration test stubs"""

    def setup(self):
        """Test case for get_echo
        Ritorna un timestamp in formato RFC5424.
        """
        for u in ("harry", "draco"):
            response = self.post(f"/user/{u}")
            self.assert200(
                response, "Response body is : " + response.data.decode("utf-8")
            )
            response = self.get(f"/user/{u}")
            self.assert200(
                response, "Response body is : " + response.data.decode("utf-8")
            )

    def test_cast_spell(self):
        response = self.post("/restart")
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))
        spells = response.json["status"]["spells"]

        for s in spells:
            data = json.dumps({"s": s}).encode()
            response = self.post("/cast/harry/draco", data=data,)
            self.assert200(
                response, "Response body is : " + response.data.decode("utf-8")
            )
            log.info(response.json)
            response = self.post("/cast/draco/harry", data=data,)
            self.assert200(
                response, "Response body is : " + response.data.decode("utf-8")
            )
            log.info(response.json)

    def test_missing(self):
        response = self.post(f"/user/harry")
        response = self.post(f"/user/draco")

        data = json.dumps({"s": "missing"}).encode()
        response = self.post("/cast/harry/harry", data=data,)
        self.assert400(response, "Response body is : " + response.data.decode("utf-8"))

    def test_get_stats(self):
        response = self.get("/user/harry")
        assert response.json["stats"]

    def test_spells(self):
        status = self.post("/restart").json
        all_spells = status["status"]["spells"]
        testlist = [
            ("abracadabra", ("avada kedavra", SPELL_KO)),
            ("avada kedavra", ("avada kedavra", SPELL_OK)),
            (
                "questo incantesimo non esiste",
                ("questo incantesimo non esiste", SPELL_MISSING),
            ),
        ]
        for test, expected in testlist:
            assert _misspelt(test, all_spells) == expected
