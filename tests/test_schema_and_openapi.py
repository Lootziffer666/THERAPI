import unittest

from therapi.openapi import OpenApiGenerator
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


if __name__ == "__main__":
    unittest.main()
