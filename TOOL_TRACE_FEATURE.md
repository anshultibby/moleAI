# Tool Execution Trace Feature

## Overview
Enhanced user experience with real-time tool execution tracing. All tool calls and their results now appear on the right side as collapsible cards, giving users full visibility into what the AI agent is doing.

## Features

### 1. **Real-time Tool Tracking**
- Every tool call is tracked with a unique ID
- Shows current execution status (Running, Completed, Error)
- Live updates as tools execute

### 2. **Collapsible Cards**
Each tool execution is displayed as a card with:
- **Header**: Tool name, icon, and status badge
- **Arguments Section**: Shows all input parameters passed to the tool
- **Result Section**: Displays the tool's output (JSON formatted if applicable)
- **Error Section**: Shows errors if the tool fails
- **Timestamp**: When the tool was executed

### 3. **All Tools Supported**
Unlike the previous version that only showed search and scraping tools, this now shows:
- `search_web_tool` - Web searches
- `scrape_website` - Website scraping
- `extract_products` - Product extraction
- `get_resource` - Resource retrieval
- `create_checklist` - Checklist creation
- `update_checklist_item` - Checklist updates
- Any other tools registered in the system

### 4. **Resizable Panel**
- Users can drag the left edge to resize the panel
- Width ranges from 320px to 800px
- Persists during the session

### 5. **Smart Grouping**
- Header shows total tool calls and breakdown by status
- Active indicator when tools are running
- Clean, modern design that matches the app theme

## Technical Implementation

### Backend Changes (`backend/app/modules/agent.py`)
1. **Enhanced `execute_tool_call` method**:
   - Now includes tool arguments in the "started" event
   - Sends arguments via `progress.arguments` field

2. **Improved result streaming**:
   - Results are truncated to 1000 chars to prevent overwhelming the UI
   - Full results are still available in chat history

### Frontend Changes

#### 1. **Type Updates** (`frontend/src/types/index.ts`)
- Added `arguments` field to `ToolExecutionEvent.progress`
- Added `tool_call_id` and `timestamp` fields

#### 2. **Hook Updates** (`frontend/src/hooks/useChat.ts`)
- Uses `tool_call_id` for unique tracking instead of generated keys
- Captures timestamp and all metadata

#### 3. **New Side Panel** (`frontend/src/components/ToolExecutionSidePanel.tsx`)
Completely redesigned with:
- Tool metadata system for icons and display names
- Collapsible card component
- JSON formatting for structured results
- Status-based color coding
- Resizable panel functionality

## Usage

When the agent executes tools, the side panel automatically appears on the right side:
1. Click on any card to expand and see full details
2. View input arguments to understand what was requested
3. View results to see what the tool returned
4. Monitor status badges to track progress

## Benefits

✅ **Transparency**: Users can see exactly what the AI is doing
✅ **Debugging**: Easy to identify issues with specific tool calls
✅ **Trust**: Builds confidence by showing the agent's reasoning process
✅ **Learning**: Users can understand how the system works
✅ **Monitoring**: Real-time feedback on long-running operations

## Future Enhancements
- Export tool trace as JSON for debugging
- Filter tools by category or status
- Expand/collapse all cards at once
- Search within tool results
- Copy arguments/results to clipboard
