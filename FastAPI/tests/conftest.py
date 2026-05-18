import sys
import os
from unittest.mock import patch, MagicMock


sys.modules['easyocr'] = MagicMock()
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))