# Tool Trace Display Bug Fix

## Problem
Search results were showing as raw Python dictionary string instead of beautiful formatted cards:

```
{'query': 'elegant black dresses', 'results': [{'title': 'Women\'s Black...
```

## Root Cause
The backend was converting tool results to strings using Python's `str()` function:

```python
result_str = str(tool_result)  # ❌ Creates {'key': 'value'} format
```

This produces Python's representation with **single quotes**, which:
- ❌ Cannot be parsed as JSON (JSON requires double quotes)
- ❌ Breaks the frontend's JSON.parse() 
- ❌ Results in displaying raw text instead of formatted cards

## Solution
Changed to use proper JSON serialization:

```python
if isinstance(tool_result, (dict, list)):
    result_str = json.dumps(tool_result, ensure_ascii=False)  # ✅ Valid JSON
else:
    result_str = str(tool_result)
```

### Changes Made
**File: `backend/app/modules/agent.py`**

1. **JSON Serialization**: Dictionaries and lists now use `json.dumps()`
2. **Increased Limit**: Truncation increased from 1000 to 2000 chars
3. **Unicode Support**: Added `ensure_ascii=False` for proper international character handling

## Result
Now search results display as beautiful, clickable cards:

```
┌────────────────────────────────────────────────────┐
│ 🔗 Women's Black Dresses Under $100               │
│    Shop elegant black dresses for any occasion    │
│    https://www.nordstrom.com/browse/women/...     │
├────────────────────────────────────────────────────┤
│ 🔗 Black Dresses - Express                        │
│    Find your perfect black dress at Express       │
│    https://www.express.com/womens-clothing/...    │
└────────────────────────────────────────────────────┘
```

## Technical Details

### Before
```python
>>> result = {'query': 'test', 'results': [...]}
>>> str(result)
"{'query': 'test', 'results': [...]}"  # Single quotes - not JSON!
>>> JSON.parse(str(result))  # ❌ Fails
```

### After
```python
>>> result = {'query': 'test', 'results': [...]}
>>> json.dumps(result)
'{"query": "test", "results": [...]}'  # Double quotes - valid JSON!
>>> JSON.parse(json.dumps(result))  # ✅ Works!
```

## Impact
- ✅ Search results display properly
- ✅ Scraped sites show formatted
- ✅ All dict/list results are JSON-compatible
- ✅ Plain text results still work as before
- ✅ International characters preserved

## Testing
Restart the backend and try any search query:
```
"Find me elegant black dresses under $100"
```

The tool trace panel will now show beautiful, clickable search result cards! 🎉
