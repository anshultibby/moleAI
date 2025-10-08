# Tool Execution Trace - Visual Guide

## Panel Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Chat Interface                    │  Tool Execution Trace             │
│                                    │  ┌─────────────────────────────┐  │
│  User: Find me red dresses         │  │ 🔧 Tool Execution Trace     │  │
│                                    │  │ 3 tool calls · 2 completed  │  │
│  Assistant: Let me search...       │  │ · 1 running                 │  │
│                                    │  └─────────────────────────────┘  │
│  [Product Grid appears here]       │                                   │
│                                    │  ┌─────────────────────────────┐  │
│                                    │  │ 🔍 Web Search       ✅ Done │  │
│                                    │  │ query: red dresses online   │  │
│                                    │  │                    [▼]       │  │
│                                    │  └─────────────────────────────┘  │
│                                    │                                   │
│                                    │  ┌─────────────────────────────┐  │
│                                    │  │ 🌐 Scrape Website   ⏳ Run  │  │
│                                    │  │ url: zara.com              │  │
│                                    │  │                    [▼]       │  │
│                                    │  └─────────────────────────────┘  │
│                                    │                                   │
│                                    │  ┌─────────────────────────────┐  │
│                                    │  │ 🛍️ Extract Products ✅ Done │  │
│                                    │  │ source: zara_content        │  │
│                                    │  │                    [▼]       │  │
│                                    │  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Collapsed Card Example

```
┌─────────────────────────────────────────────┐
│ 🔍  Web Search         ✅ Completed         │
│     query: red dresses online          [▼]  │
└─────────────────────────────────────────────┘
```

## Expanded Card Example

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🔍  Web Search                      ✅ Completed              [▲]   │
├─────────────────────────────────────────────────────────────────────┤
│ INPUT ARGUMENTS                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ query: "red dresses online"                                     │ │
│ │ max_results: 10                                                 │ │
│ └─────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│ RESULT                                                              │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ {                                                               │ │
│ │   "query": "red dresses online",                               │ │
│ │   "results": [                                                 │ │
│ │     {                                                          │ │
│ │       "title": "Zara Red Dresses",                            │ │
│ │       "url": "https://zara.com/dresses/red",                  │ │
│ │       "description": "Shop the latest red dresses..."         │ │
│ │     },                                                         │ │
│ │     ...                                                        │ │
│ │   ]                                                            │ │
│ │ }                                                              │ │
│ └─────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│ 2:45:32 PM                                                          │
└─────────────────────────────────────────────────────────────────────┘
```

## Status Indicators

### Running (Blue)
```
⏳ Running
```
- Tool is currently executing
- Animated pulse indicator in header

### Completed (Green)
```
✅ Completed
```
- Tool finished successfully
- Result section is available

### Error (Red)
```
❌ Error
```
- Tool encountered an error
- Error message displayed in red section

### In Progress (Yellow)
```
⚙️ In Progress
```
- Tool is processing (for long-running operations)
- May show progress percentage

## Color Scheme

### Light Mode
- Card background: White
- Card border: Light gray
- Status badges: Colored backgrounds with darker text
- Panel background: Gradient from slate-50 to white

### Dark Mode
- Card background: slate-800
- Card border: slate-700
- Status badges: Semi-transparent colored backgrounds
- Panel background: Gradient from slate-900 to slate-800

## Interactive Features

1. **Click header** → Expand/collapse card
2. **Drag left edge** → Resize panel (320px - 800px)
3. **Scroll** → View all tool executions
4. **Auto-hide** → Panel disappears when no tools are running

## Tool Icons Reference

| Tool | Icon | Category |
|------|------|----------|
| search_web_tool | 🔍 | Search |
| scrape_website | 🌐 | Extraction |
| extract_products | 🛍️ | Extraction |
| get_resource | 📦 | Data |
| create_checklist | ✅ | Planning |
| update_checklist_item | 📝 | Planning |
| (default) | 🔧 | Tool |
