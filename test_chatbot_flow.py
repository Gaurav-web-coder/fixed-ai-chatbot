import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import gemini_client as chat


class GeminiTests(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.client.models.generate_content.return_value.text = "Gemini answer"
        genai = ModuleType("google.genai")
        genai.Client = MagicMock()
        genai.Client.return_value.__enter__.return_value = self.client
        types = SimpleNamespace(
            Content=lambda **kw: kw,
            Part=SimpleNamespace(from_text=lambda **kw: kw),
            HttpOptions=lambda **kw: kw,
            GenerateContentConfig=lambda **kw: kw,
        )
        genai.types = types
        google = ModuleType("google")
        google.genai = genai
        self.modules = patch.dict(sys.modules, {"google": google, "google.genai": genai})
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def test_gemini_only_with_history_and_single_current_question(self):
        answer = chat.generate_response("follow up", "test-key", [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ])
        self.assertEqual(answer, "Gemini answer")
        self.client.models.generate_content.assert_called_once()
        contents = self.client.models.generate_content.call_args.kwargs["contents"]
        self.assertEqual([x["role"] for x in contents], ["user", "model", "user"])
        self.assertEqual(contents[-1]["parts"], [{"text": "follow up"}])

    def test_missing_key_makes_no_request(self):
        with self.assertRaisesRegex(chat.GeminiError, "GEMINI_API_KEY"):
            chat.generate_response("hi")
        self.client.models.generate_content.assert_not_called()

    def test_failure_visible_key_hidden_and_no_duplicate_retry(self):
        exc = RuntimeError("Quota exceeded for test-key")
        exc.code = 429
        self.client.models.generate_content.side_effect = exc
        with self.assertRaises(chat.GeminiError) as caught:
            chat.generate_response("hi", "test-key")
        self.assertIn("429", str(caught.exception))
        self.assertIn("Quota exceeded", str(caught.exception))
        self.assertNotIn("test-key", str(caught.exception))
        self.client.models.generate_content.assert_called_once()

    def test_empty_response_is_error(self):
        self.client.models.generate_content.return_value.text = None
        with self.assertRaisesRegex(chat.GeminiError, "no text"):
            chat.generate_response("hi", "test-key")

    def test_model_override(self):
        chat.generate_response("hi", "test-key", model="chosen-model")
        self.assertEqual(self.client.models.generate_content.call_args.kwargs["model"], "chosen-model")


if __name__ == "__main__":
    unittest.main()
