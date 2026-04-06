import tempfile
import unittest

from therapi.openapi import OpenApiGenerator
from therapi.redaction import REDACTED, redact_headers, redact_json
from therapi.ai_clients import build_insight_engine
from therapi.listener import AutoListener
from therapi.proxy import _load_ui_page, _rewrite_ui_links, _ui_html_filename
from therapi.registry import SchemaRegistry
from therapi.service_directory import ServiceDirectory
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


class UiRoutingTests(unittest.TestCase):
    def test_ui_route_defaults_to_control_panel(self):
        self.assertEqual(_ui_html_filename("/_therapi/ui"), "control-panel.html")
        self.assertEqual(_ui_html_filename("/_therapi/ui/"), "control-panel.html")

    def test_ui_route_rejects_invalid_paths(self):
        self.assertIsNone(_ui_html_filename("/_therapi/ui/../settings.html"))
        self.assertIsNone(_ui_html_filename("/_therapi/ui/nested/control-panel.html"))

    def test_ui_link_rewrite_points_to_runtime_route(self):
        html = '<a href="schema-drift.html">Schema Drift</a>'
        rewritten = _rewrite_ui_links(html)
        self.assertIn('href="/_therapi/ui/schema-drift.html"', rewritten)

    def test_load_ui_page_uses_runtime_links(self):
        page = _load_ui_page("schema-drift.html")
        self.assertIsNotNone(page)
        self.assertIn('href="/_therapi/ui/control-panel.html"', page)


class _FakeInsightEngine:
    def __init__(self):
        self.prompt = None

    def generate(self, prompt: str) -> str:
        self.prompt = prompt
        return "Use canary tests for removed fields first."


class ListenerTests(unittest.TestCase):
    def test_listener_builds_fallback_report(self):
        registry = SchemaRegistry()
        registry.observe("GET", "/users", None, {"id": 1})

        listener = AutoListener(registry, interval_seconds=60)
        listener.tick()
        report = listener.latest_insights()

        self.assertEqual(report["source"], "local-fallback")
        self.assertIn("endpoint", report["recommendation"].lower())

    def test_listener_uses_ai_engine_when_available(self):
        registry = SchemaRegistry()
        registry.observe("GET", "/users", None, {"id": 1})

        engine = _FakeInsightEngine()
        listener = AutoListener(registry, interval_seconds=60, insight_engine=engine)
        listener.tick()
        report = listener.latest_insights()

        self.assertEqual(report["source"], "ai")
        self.assertIn("canary", report["recommendation"].lower())
        self.assertIsNotNone(engine.prompt)

    def test_build_engine_requires_provider_config(self):
        self.assertIsNone(build_insight_engine(None, None, None))
        with self.assertRaises(ValueError):
            build_insight_engine("openai", None, "gpt-4.1")


class ServiceDirectoryTests(unittest.TestCase):
    def test_defaults_include_transit_phonebook_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = ServiceDirectory(f"{tmpdir}/phonebook.json")
            apis = directory.list_apis()
            names = {item["name"] for item in apis}
            self.assertIn("AVV", names)
            self.assertIn("DB", names)
            self.assertIn("Transitous", names)

            avv = next(item for item in apis if item["name"] == "AVV")
            self.assertEqual(len(avv["services"]), 11)
            wadl_urls = {service["wadl_url"] for service in avv["services"]}
            self.assertIn("https://auskunft.avv.de/restproxy/arrivalBoard?wadl", wadl_urls)
            self.assertIn("https://auskunft.avv.de/restproxy/xsd", wadl_urls)

    def test_can_add_multiple_custom_providers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = ServiceDirectory(f"{tmpdir}/phonebook.json")
            directory.add_provider("custom-a", "https://llm-a.example.com", model="a-model")
            directory.add_provider("custom-b", "https://llm-b.example.com", model="b-model")

            providers = directory.list_providers()
            self.assertEqual(len(providers), 2)


if __name__ == "__main__":
    unittest.main()
