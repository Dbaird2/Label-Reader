import sys
import os
from unittest.mock import patch, MagicMock


sys.modules['easyocr'] = MagicMock()
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key-for-testing"
mock_ai_agent = MagicMock()
mock_ai_agent.agent = MagicMock()
sys.modules["services.AI_agent"] = mock_ai_agent
