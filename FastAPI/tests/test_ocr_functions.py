import pytest
from ocr_services.ocr_functions import find_best_match, get_candidates, filterString
from unittest.mock import patch, AsyncMock
import state

@pytest.mark.asyncio
async def test_find_best_match():
    candidates = ['Seth', 'Seth Alison', 'Seth A.']

    fake_db_response = {'name': 'Seth Alison', 'department': 'Theatreworks', 'building': 'Arts Center', 'confidence': 1.0}

    with patch.object(state.db, "lookupName", new=AsyncMock(return_value=fake_db_response)):
        best_match = await find_best_match(candidates)
        assert best_match['department'] == 'Theatreworks'

@pytest.mark.asyncio
async def test_find_best_match_no_confidence():
    candidates = []

    fake_db_response = {}

    with patch.object(state.db, "lookupName", new=AsyncMock(return_value=fake_db_response)):
        best_match = await find_best_match(candidates)
        assert best_match == None

def test_candidates():
    candidates = ['Theatreworks', 'Seth Alison', 'Colorado', 'Bob']

    fake_res = ['Theatreworks', 'Seth Alison', 'Colorado', 'Bob', 
                'Theatreworks Seth Alison', 'Seth Alison Colorado', 'Colorado Bob', 
                'Theatreworks Seth Alison Colorado', 'Seth Alison Colorado Bob']

    candidates = get_candidates(candidates)
    print(candidates)
    assert fake_res == candidates

def test_candidates_single():
    candidates = ['Seth Alison']

    fake_res = ['Seth Alison']

    candidates = get_candidates(candidates)
    print(candidates)
    assert fake_res == candidates

def test_candidates_empty():
    candidates = []
    fake_res = []
    candidates = get_candidates(candidates)
    print(candidates)
    assert fake_res == candidates

def test_filterString():
    assert filterString("Seth Alison") == True
    assert filterString("S3th @lison") == False
    assert filterString("Seth A.") == False
    assert filterString("Seth, Alison") == True
    assert filterString("Seth Alison Colorado") == True