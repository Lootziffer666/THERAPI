import unittest

from therapi.openapi import OpenApiGenerator
from therapi.redaction import REDACTED, redact_headers, redact_json
from therapi.registry import SchemaRegistry
from therapi.schema import SchemaNode


class SchemaInferenceTests(unittest.TestCase):
    def test_optional_field_tracking(self):
        node = SchemaNode()
        node.observe({"id": 1, "name": "a"})
        node.observe({"id": 2})

        schema = node.to_openapi_schema(required_threshold=0.95)
        self.assertEqual(schema["type"], "object")
        self.assertIn("id", schema["required"])
        self.assertNotIn("name", schema.get("required", []))


class RegistryAndOpenApiTests(unittest.TestCase):
    def test_versions_and_openapi_generation(self):
        registry = SchemaRegistry()
        changed_1 = registry.observe("GET", "/users", None, {"id": 1, "name": "Jane"})
        changed_2 = registry.observe("GET", "/users", None, {"id": 2, "name": "John"})
        changed_3 = registry.observe("GET", "/users", None, {"id": 3, "name": "John", "active": True})

        self.assertTrue(changed_1)
        self.assertFalse(changed_2)
        self.assertTrue(changed_3)

        spec = OpenApiGenerator(registry).generate()
        get_users = spec["paths"]["/users"]["get"]
        properties = get_users["responses"]["200"]["content"]["application/json"]["schema"]["properties"]
        self.assertIn("active", properties)

    def test_drift_report_contains_changes(self):
        registry = SchemaRegistry()
        registry.observe("GET", "/users", None, {"id": 1})
        registry.observe("GET", "/users", None, {"id": 1, "name": "Jane"})

        drift = registry.drift_report()["GET /users"]
        self.assertEqual(len(drift), 2)
        self.assertTrue(any("name:string" in item for item in drift[-1]["response"]["added"]))

    def test_collection_export_stores_redacted_capture(self):
        registry = SchemaRegistry()
        registry.observe(
            "POST",
            "/login",
            {"username": "alice", "password": "secret"},
            {"token": "abc"},
            capture={
                "target": "https://example.com/login",
                "status": 200,
                "request_headers": redact_headers({"Authorization": "Bearer x", "X-Trace": "1"}),
                "response_headers": {},
                "request_json": redact_json({"password": "secret", "username": "alice"}),
                "response_json": redact_json({"token": "abc"}),
            },
        )

        exported = registry.export_collections()["collections"][0]["captures"][0]
        self.assertEqual(exported["request_headers"]["Authorization"], REDACTED)
        self.assertEqual(exported["request_json"]["password"], REDACTED)
        self.assertEqual(exported["response_json"]["token"], REDACTED)


if __name__ == "__main__":
    unittest.main()
