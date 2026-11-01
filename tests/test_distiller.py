import unittest
from mcp_context_distiller.distiller import distill_schema, distill_output, ContextDistiller


class TestDistiller(unittest.TestCase):
    def test_schema_compaction(self):
        verbose_schema = {
            "type": "object",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "UnnecessaryTitle",
            "description": "This is a very long descriptive paragraph intended for humans. It goes on and on about details the model does not strictly require. Another sentence follows.",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Unique identifier of user. Never share outside trusted networks.",
                    "default": None,
                    "empty_list": []
                },
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "description": "Tag string."
                    }
                }
            },
            "required": ["user_id"]
        }

        compact = distill_schema(verbose_schema, mode="compact")
        self.assertNotIn("title", compact)
        self.assertNotIn("$schema", compact)
        self.assertIn("user_id", compact["properties"])
        self.assertNotIn("empty_list", compact["properties"]["user_id"])
        self.assertEqual(compact["properties"]["user_id"]["description"], "Unique identifier of user")

        minimal = distill_schema(verbose_schema, mode="minimal")
        self.assertNotIn("description", minimal["properties"]["user_id"])
        self.assertIn("required", minimal)

    def test_output_condensation(self):
        oversized_output = {
            "status": "success",
            "records": [
                {"id": i, "name": f"Item {i}", "blob": "X" * 500} for i in range(50)
            ],
            "empty_val": None
        }

        distilled = distill_output(oversized_output, max_array_items=4, truncate_strings=50)
        self.assertNotIn("empty_val", distilled)
        self.assertEqual(len(distilled["records"]), 5) # 2 head + 1 marker + 2 tail
        self.assertIn("...[46 items omitted for brevity]...", distilled["records"])
        self.assertTrue("...[+450 chars truncated]" in distilled["records"][0]["blob"])


if __name__ == "__main__":
    unittest.main()
