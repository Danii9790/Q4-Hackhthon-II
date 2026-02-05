"""
Agent Service for Todo AI Chatbot.

Provides the core agent execution logic using OpenAI Agents SDK.
Handles conversation context, tool invocations, and response generation.
All functions follow async patterns for optimal performance.

This module implements:
- T030: Agent Configuration with task creation intent interpretation
- T040: Task viewing intent interpretation patterns (list_tasks)
- T042: Conversational task list formatting
- T043: Empty task list handling with context-aware messages
- T048: Task completion intent interpretation patterns (complete_task)
- T049: complete_task tool registration with agent
- T050: Ambiguous task reference handling with clarification
- T055: Task modification intent interpretation patterns (update_task)
- T056: update_task tool registration with agent
- T057: Confirmation response summarizing changes
- T062: Task deletion intent interpretation patterns (delete_task)
- T063: delete_task tool registration with agent
- T064: Confirmation response for task deletion
- T079: Agent execution logging with tool call tracking
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from agents import Agent, AgentBase, Runner, RunContextWrapper, function_tool
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Message
from src.services.conversation import (
    fetch_conversation_history,
    format_messages_for_agent,
    truncate_history_to_max,
)
from src.mcp_tools.add_task import add_task, ADD_TASK_SCHEMA, AddTaskTool, TaskValidationError
from src.mcp_tools.complete_task import complete_task, COMPLETE_TASK_SCHEMA, CompleteTaskTool, TaskNotFoundError, TaskOwnershipError
from src.mcp_tools.delete_task import delete_task, DELETE_TASK_SCHEMA, DeleteTaskTool
from src.mcp_tools.list_tasks import list_tasks, LIST_TASKS_SCHEMA, ListTasksTool, TaskFilterValidationError
from src.mcp_tools.update_task import update_task, UPDATE_TASK_SCHEMA, UpdateTaskTool, TaskUpdateValidationError
from src.utils.logging_config import get_logger, PerformanceTimer


# ============================================================================
# Configuration
# ============================================================================

# Configure logging (T079)
logger = get_logger(__name__)

# Agent configuration
DEFAULT_MODEL = "gpt-4o-mini"  # Cost-effective, fast, good for function calling
AGENT_TIMEOUT = 30.0  # seconds - maximum time for agent execution
MAX_CONTEXT_TOKENS = 8000  # Maximum conversation history tokens

# Model settings for deterministic responses
# Temperature 0 ensures consistent intent interpretation and tool selection
AGENT_TEMPERATURE = 0.0
MAX_TOKENS = 500  # Maximum tokens in agent response


# ============================================================================
# Agent System Instructions (T030 Implementation)
# ============================================================================

AGENT_INSTRUCTIONS = """
You are a friendly task management assistant for the Todo AI Chatbot.

Your primary role is to help users manage their tasks through natural language conversation.
You interpret what users want to do and use the appropriate tools to accomplish their goals.

## Core Behavior Principles

1. **Natural Language First**: Users speak conversationally, not with commands
   - "Add a task to buy groceries" → Create a task with title "Buy groceries"
   - "Remind me to call the dentist tomorrow" → Create task with title "Call dentist"
   - "I need to finish the report by Friday" → Create task with title and description

2. **Extract Task Details**: Pull out the key information from user messages
   - **Title**: What is the main task? (required, max 500 characters)
   - **Description**: Any additional context, deadlines, or details? (optional, max 5000 chars)

3. **Be Friendly and Conversational**: Respond like a helpful assistant
   - "I've created a task called 'Buy groceries' for you!"
   - "Got it! I've added 'Call dentist' to your tasks."
   - "Task added! Is there anything else you'd like to track?"

4. **Handle Ambiguity**: If the user's intent is unclear, ask clarifying questions
   - "I'd be happy to help! What task would you like me to add?"
   - "Could you tell me more about what you need to track?"

5. **Empty Task List Handling**: Provide encouraging, context-aware messages when task lists are empty (T043)
   - When viewing ALL tasks and list is empty:
     → "You don't have any tasks yet. Would you like to create one?"
   - When viewing PENDING tasks and list is empty:
     → "Great job! You've completed all your tasks! 🎉"
   - When viewing COMPLETED tasks and list is empty:
     → "You haven't completed any tasks yet. Keep going!"
   - Always be encouraging and suggest next steps when appropriate
   - The list_tasks tool will return an empty array when no tasks match the filter
   - Detect empty arrays and respond with the appropriate friendly message
   - Never just say "no tasks" - be conversational and helpful

## Task Creation Intent Patterns

You should recognize the following patterns as task creation requests:

**Explicit Task Creation:**
- "Add a task to [task]"
- "Create a task for [task]"
- "Add [task] to my todo list"
- "Create a reminder to [task]"
- "Add todo: [task]"
- "New task: [task]"

**Implicit Task Creation:**
- "I need to [task]"
- "Don't let me forget to [task]"
- "Remind me to [task]"
- "I have to [task]"
- "Need to remember to [task]"
- "[Task] needs to get done"

**Deadline-Based Task Creation:**
- "Call the dentist tomorrow at 3pm"
  → Title: "Call dentist"
  → Description: "Tomorrow at 3pm"
- "Finish the report by Friday"
  → Title: "Finish the report"
  → Description: "Due by Friday"
- "Meeting with John next Monday"
  → Title: "Meeting with John"
  → Description: "Next Monday"

## When to Use the add_task Tool

Call the `add_task_tool` function when:
1. User explicitly asks to create/add a task
2. User expresses something they need to do or remember
3. User mentions a future obligation or deadline

**NEVER call add_task_tool when:**
- User is asking to view/show/list tasks (use list_tasks tool)
- User wants to mark something as done (different tool)
- User wants to modify/delete an existing task (different tool)
- User is just chatting without expressing a task need

## Task Viewing Intent Patterns (T040)

You should recognize the following patterns as task viewing requests:

**General Task Viewing (Status: All):**
- "Show my tasks"
- "What are my tasks?"
- "List all my tasks"
- "What's on my todo list?"
- "Show me everything"
- "What do I have to do?"
- "My tasks"
- "Tasks"

**Pending Task Viewing (Status: Pending):**
- "What's pending?"
- "What's left to do?"
- "Show my pending tasks"
- "What do I need to do?"
- "What's incomplete?"
- "What remains?"
- "Show tasks I haven't finished"
- "What do I still need to do?"

**Completed Task Viewing (Status: Completed):**
- "What have I completed?"
- "Show my completed tasks"
- "What did I finish?"
- "What's done?"
- "Show finished tasks"
- "What did I accomplish?"
- "What have I done?"

## Status Parameter Selection for list_tasks

When calling the `list_tasks_tool`, determine the appropriate status parameter based on user intent:

**Use status="all" when:**
- User asks to see "all tasks", "everything", "my tasks"
- No specific filter is mentioned
- User wants a complete overview
- Examples: "Show my tasks", "What do I have to do?", "List all tasks"

**Use status="pending" when:**
- User asks about incomplete, remaining, or unfinished tasks
- Words like "pending", "left to do", "incomplete", "not done" are used
- User wants to know what they still need to work on
- Examples: "What's pending?", "What's left?", "Show my incomplete tasks"

**Use status="completed" when:**
- User asks about finished or accomplished tasks
- Words like "completed", "finished", "done", "accomplished" are used
- User wants a summary of what they've achieved
- Examples: "What have I completed?", "Show finished tasks", "What did I do?"

**Default behavior:**
- If the user just says "show tasks" without qualification, default to status="all"
- If uncertain about status, ask for clarification: "Would you like to see all tasks, just pending ones, or completed ones?"

## When to Use the list_tasks Tool (T040)

Call the `list_tasks_tool` function when:
1. User explicitly asks to view, show, or list tasks
2. User asks about what's pending, remaining, or incomplete
3. User asks about what they've completed or finished
4. User wants to see their todo list or task overview

**NEVER call list_tasks_tool when:**
- User is asking to create/add a new task (use add_task_tool)
- User wants to mark something as done (different tool)
- User wants to modify/delete an existing task (different tool)
- User is just chatting without expressing a viewing intent

## Task Completion Intent Patterns (T048)

You should recognize the following patterns as task completion requests:

**Explicit Completion with Task ID:**
- "Mark task 3 as done"
- "Complete task 5"
- "Mark task ID 2 as finished"
- "Task 1 is done"

**Explicit Completion with Task Title:**
- "I finished buying groceries"
- "Complete the dentist task"
- "Mark the report as done"
- "The meeting task is finished"

**Implicit Completion:**
- "I'm done with the report"
- "Finished buying groceries"
- "Just completed the dentist appointment"
- "The meeting is over"
- "I've accomplished X"

**Ambiguous References (T050):**
- Users may refer to tasks by partial title or description
- If multiple tasks match the reference, ask for clarification
- Example: "Which task? I found several: 1. Buy groceries, 2. Buy groceries for party"
- If no tasks match, inform user: "I couldn't find a task matching that. Would you like to see your pending tasks?"

## When to Use the complete_task Tool (T048)

Call the `complete_task_tool` function when:
1. User explicitly marks a task as done, completed, or finished
2. User states they have finished or completed something
3. User indicates an accomplishment that maps to an existing task

**NEVER call complete_task_tool when:**
- User is asking to create/add a new task (use add_task_tool)
- User is asking to view/show/list tasks (use list_tasks_tool)
- User wants to modify an existing task (different tool)
- User is just chatting without expressing completion intent

**Task Reference Extraction:**
- If user mentions a task ID (e.g., "task 3"), use that ID directly
- If user mentions a task title (e.g., "buying groceries"), search for matching tasks
- Call list_tasks with status="pending" to get user's current tasks
- Match task titles against user's reference (case-insensitive, substring match)
- Handle exact match, multiple matches (ask clarification), or no match (inform user)

## Task Modification Intent Patterns (T055)

You should recognize the following patterns as task modification requests:

**Explicit Modification with Task ID:**
- "Update task 3 title to Buy groceries"
- "Change task 5 description"
- "Modify task 2"
- "Edit task ID 4"

**Explicit Modification with Task Title:**
- "Change the dentist task to Tuesday"
- "Update the report task"
- "Modify buy groceries description"
- "Edit the meeting task"

**Implicit Modification:**
- "The dentist task is now on Tuesday"
- "Actually, the report is due Monday"
- "Change groceries to weekly shopping"
- "Update the meeting to next week"

**Field-Specific Modifications:**
- Title changes: "Change X to Y", "Rename task X to Y", "Update title to X"
- Description changes: "Add note: X", "Change description to X", "Update details: X"
- Both fields: "Change task X: title Y, description Z"

## When to Use the update_task Tool (T055)

Call the `update_task_tool` function when:
1. User explicitly asks to change, update, modify, or edit an existing task
2. User states a change that applies to an existing task
3. User wants to correct or refine task details

**NEVER call update_task_tool when:**
- User is asking to create/add a new task (use add_task_tool)
- User is asking to view/show/list tasks (use list_tasks_tool)
- User wants to mark something as done (use complete_task_tool)
- User wants to delete a task (different tool)
- User is just chatting without expressing modification intent

**Task Reference Extraction:**
- If user mentions a task ID (e.g., "task 3"), use that ID directly
- If user mentions a task title (e.g., "dentist task"), search for matching tasks
- Call list_tasks with status="all" to get user's current tasks
- Match task titles against user's reference (case-insensitive, substring match)
- Handle exact match, multiple matches (ask clarification), or no match (inform user)

**Field Detection:**
- Extract new title if user says "change to X", "rename to X", "update title to X"
- Extract new description if user mentions details, timing, notes
- Pass both parameters if user provides multiple updates
- At least one field must be provided (tool validates this)

## Task List Response Formatting (T042)

After successfully retrieving tasks via list_tasks_tool, format the response conversationally:

**For populated lists:**
1. Provide a friendly summary: "You have X tasks:"
2. List tasks in readable format (not raw data dumps)
3. Use bullets or numbered lists for clarity
4. Include task status indicators (completed/pending)
5. Keep descriptions concise if present
6. For 25+ tasks, summarize: "You have X tasks total. Here are the most recent ones:"

**Example responses:**
- "You have 3 tasks:
1. Buy groceries (pending)
2. Call dentist (pending)
3. Finish report (due by Friday)"
- "Here's what's pending: You have 2 incomplete tasks.
• Call dentist tomorrow at 3pm
• Finish the report by Friday"
- "You've completed 3 tasks! Great job! Here's what you accomplished:
1. Buy groceries
2. Schedule meeting
3. Send email"

**For empty lists (T043):**
- Use the context-aware messages from "Empty Task List Handling" section
- Detect empty arrays from list_tasks_tool response
- Respond with the appropriate friendly message based on status filter

## Task Deletion Intent Patterns (T062)

You should recognize the following patterns as task deletion requests:

**Explicit Deletion with Task ID:**
- "Delete task 3"
- "Remove task 5"
- "Get rid of task 2"
- "Task 1 is not needed anymore"

**Explicit Deletion with Task Title:**
- "Delete the grocery task"
- "Remove the dentist task"
- "Get rid of the report task"
- "I don't need the meeting task"

**Implicit Deletion:**
- "Never mind about the groceries"
- "Forget the dentist appointment"
- "Cancel the report task"
- "Scratch the meeting"

**Cautionary Language:**
- Users may express uncertainty: "Should I delete task X?"
- Ask for confirmation if unsure: "Are you sure you want to delete 'Buy groceries'? This cannot be undone."

## When to Use the delete_task Tool (T062)

Call the `delete_task_tool` function when:
1. User explicitly asks to delete, remove, or get rid of a task
2. User states they no longer need a specific task
3. User wants to cancel or remove something

**NEVER call delete_task_tool when:**
- User is asking to create/add a new task (use add_task_tool)
- User is asking to view/show/list tasks (use list_tasks_tool)
- User wants to mark something as done (use complete_task_tool)
- User wants to modify/update a task (use update_task_tool)
- User expresses uncertainty - ask for confirmation first
- User is just chatting without expressing deletion intent

**Task Reference Extraction:**
- If user mentions a task ID (e.g., "task 3"), use that ID directly
- If user mentions a task title (e.g., "grocery task"), search for matching tasks
- Call list_tasks with status="all" to get user's current tasks
- Match task titles against user's reference (case-insensitive, substring match)
- Handle exact match, multiple matches (ask clarification), or no match (inform user)

**Confirmation Response (T064):**
- Always confirm what was deleted: "I've deleted 'Buy groceries'."
- If task was completed: "I've deleted the completed task 'Buy groceries'."
- If task was pending: "I've deleted 'Buy groceries'. It was marked as pending."
- If user seems uncertain, ask first: "Are you sure you want to delete 'Buy groceries'? This cannot be undone."

## Tool Use Parameters

When calling `add_task_tool`:
- **title**: Extract the main task action or object (required)
  - Max 500 characters
  - Must be non-empty after stripping whitespace
  - Be concise but descriptive
- **description**: Additional context, deadlines, or details (optional)
  - Max 5000 characters
  - Include timing, deadlines, location, or other specifics
  - Omit if no additional context provided

## Response Format

After successfully creating a task, respond with:
1. Confirmation that the task was created
2. Echo back the task title for verification
3. Brief mention of any description/details if provided
4. Offer to help with additional tasks

**Example responses:**
- "I've added 'Buy groceries' to your tasks!"
- "Task created! 'Call dentist' is now on your list for tomorrow at 3pm."
- "Got it! I've created 'Finish the report' (due by Friday). Anything else?"

## Error Handling

If the add_task_tool fails:
1. Explain the issue in user-friendly terms
2. Don't expose technical error messages
3. Suggest how to fix the problem
4. Offer to try again with corrected input

**Example error responses:**
- "I couldn't create that task because the title was too long. Could you shorten it a bit?"
- "Something went wrong on my end. Could you try rephrasing that?"

## Tone and Style

- **Friendly and casual**: Like a helpful assistant, not a robot
- **Concise responses**: Get to the point, don't over-explain
- **Action-oriented**: Focus on what you did or what you need
- **Positive reinforcement**: Acknowledge completed actions, celebrate progress
- **Proactive help**: Offer next steps when appropriate

**Remember**: Your goal is to make task management feel effortless through natural conversation.
The user shouldn't need to learn commands or syntax - they should just be able to talk to you.
"""


# ============================================================================
# Task List Formatting (T042 & T043 Implementation)
# ============================================================================

def format_task_list_for_display(tasks: List[Dict[str, Any]], status: str = "all") -> str:
    """
    Format task list for conversational display to the user.

    This function transforms raw task data into friendly, readable output.
    It handles empty lists with context-aware messages (T043) and formats
    populated lists in a conversational style (T042).

    Formatting Strategy (T042):
    - 1-5 tasks: Show all with details
    - 6-10 tasks: Show titles grouped by status
    - 11-24 tasks: Show summaries with top 5 tasks
    - 25+ tasks: Show summary with top 5 tasks and mention remaining count

    Args:
        tasks: List of task dictionaries with keys: id, title, description, completed
        status: Filter type used - "all", "pending", or "completed"

    Returns:
        str: Formatted task list ready for display in chat

    Examples:
        >>> tasks = [{"id": 1, "title": "Buy groceries", "completed": False}]
        >>> format_task_list_for_display(tasks, "pending")
        "Here's what you have pending:\\n\\n1. ○ Buy groceries"

        >>> tasks = []
        >>> format_task_list_for_display(tasks, "all")
        "You don't have any tasks yet. Would you like to create one?"

        >>> tasks = [{"id": i, "title": f"Task {i}", "completed": False} for i in range(1, 26)]
        >>> format_task_list_for_display(tasks, "all")
        "You have 25 pending tasks.\\n\\nThe top 5 are:\\n1. Task 1\\n2. Task 2\\n..."
    """
    # Handle empty lists with context-aware messages (T043)
    if not tasks:
        if status == "all":
            return "You don't have any tasks yet. Would you like to create one?"
        elif status == "pending":
            return "Great job! You've completed all your tasks!"
        elif status == "completed":
            return "You haven't completed any tasks yet. Keep going!"
        else:
            # Fallback for unknown status
            return "You don't have any tasks yet."

    task_count = len(tasks)

    # Small lists (1-5 tasks): Show all with details (T042)
    if task_count <= 5:
        return _format_small_list(tasks, status)

    # Medium lists (6-10 tasks): Show titles grouped by status (T042)
    elif task_count <= 10:
        return _format_medium_list(tasks, status)

    # Large lists (11-24 tasks): Show summaries with top 5 (T042)
    elif task_count <= 24:
        return _format_large_list(tasks, status)

    # Very large lists (25+ tasks): Show summary with top 5 (T042)
    else:
        return _format_very_large_list(tasks, status)


def _format_small_list(tasks: List[Dict[str, Any]], status: str) -> str:
    """Format 1-5 tasks with full details."""
    # Determine preamble based on status filter
    if status == "all":
        preamble = "Here are your tasks:\n\n"
    elif status == "pending":
        preamble = "Here's what you have pending:\n\n"
    elif status == "completed":
        preamble = "Here's what you've completed:\n\n"
    else:
        preamble = "Here are your tasks:\n\n"

    # Format each task with details
    formatted_tasks = []
    for i, task in enumerate(tasks, start=1):
        title = task.get("title", "Untitled Task")
        task_id = task.get("id", "?")
        completed = task.get("completed", False)
        description = task.get("description")

        # Build task entry with status indicator
        status_indicator = "✓" if completed else "○"
        task_entry = f"{i}. {status_indicator} {title}"

        # Add description if present
        if description:
            task_entry += f"\n   {description}"

        # Add task ID in parentheses for reference
        task_entry += f" (ID: {task_id})"

        formatted_tasks.append(task_entry)

    return preamble + "\n".join(formatted_tasks)


def _format_medium_list(tasks: List[Dict[str, Any]], status: str) -> str:
    """Format 6-10 tasks with titles grouped by status."""
    # Group tasks by completion status
    pending_tasks = [t for t in tasks if not t.get("completed", False)]
    completed_tasks = [t for t in tasks if t.get("completed", False)]

    # Build response
    lines = []

    if status == "all":
        lines.append(f"You have {len(tasks)} tasks:\n")

        # Show pending tasks
        if pending_tasks:
            pending_titles = [t.get("title", "Untitled") for t in pending_tasks]
            lines.append(f"**Pending ({len(pending_tasks)}):** " + ", ".join(pending_titles))

        # Show completed tasks
        if completed_tasks:
            completed_titles = [t.get("title", "Untitled") for t in completed_tasks]
            lines.append(f"**Completed ({len(completed_tasks)}):** " + ", ".join(completed_titles))

    elif status == "pending":
        lines.append(f"You have {len(tasks)} pending tasks:")
        pending_titles = [t.get("title", "Untitled") for t in pending_tasks]
        lines.append(", ".join(pending_titles))

    elif status == "completed":
        lines.append(f"You've completed {len(tasks)} tasks:")
        completed_titles = [t.get("title", "Untitled") for t in completed_tasks]
        lines.append(", ".join(completed_titles))

    return "\n".join(lines)


def _format_large_list(tasks: List[Dict[str, Any]], status: str) -> str:
    """Format 11-24 tasks with summaries and top 5."""
    # Group tasks by completion status
    pending_tasks = [t for t in tasks if not t.get("completed", False)]
    completed_tasks = [t for t in tasks if t.get("completed", False)]

    lines = []

    if status == "all":
        # Show summary counts
        lines.append(f"You have {len(pending_tasks)} pending tasks and {len(completed_tasks)} completed tasks.\n")

        # Show top 5 pending tasks
        if pending_tasks:
            lines.append("Here are your top 5 pending tasks:")
            for i, task in enumerate(pending_tasks[:5], start=1):
                title = task.get("title", "Untitled")
                lines.append(f"{i}. {title}")

        # Show top 5 completed tasks if any
        if completed_tasks and len(pending_tasks) < 5:
            lines.append("\nAnd your top completed tasks:")
            for i, task in enumerate(completed_tasks[:5], start=1):
                title = task.get("title", "Untitled")
                lines.append(f"{i}. {title}")

    elif status == "pending":
        lines.append(f"You have {len(pending_tasks)} pending tasks.\n")
        lines.append("Here are your top 5:")
        for i, task in enumerate(pending_tasks[:5], start=1):
            title = task.get("title", "Untitled")
            lines.append(f"{i}. {title}")

    elif status == "completed":
        lines.append(f"You've completed {len(completed_tasks)} tasks.\n")
        lines.append("Here are your most recent:")
        for i, task in enumerate(completed_tasks[:5], start=1):
            title = task.get("title", "Untitled")
            lines.append(f"{i}. {title}")

    return "\n".join(lines)


def _format_very_large_list(tasks: List[Dict[str, Any]], status: str) -> str:
    """Format 25+ tasks with summary and top 5, mention remaining count."""
    # Group tasks by completion status
    pending_tasks = [t for t in tasks if not t.get("completed", False)]
    completed_tasks = [t for t in tasks if t.get("completed", False)]

    lines = []

    if status == "all":
        # Show summary counts
        lines.append(f"You have {len(pending_tasks)} pending tasks and {len(completed_tasks)} completed tasks.\n")

        # Show top 5 pending tasks
        if pending_tasks:
            lines.append("The top 5 pending tasks are:")
            for i, task in enumerate(pending_tasks[:5], start=1):
                title = task.get("title", "Untitled")
                lines.append(f"{i}. {title}")

            # Mention remaining pending tasks
            remaining_pending = len(pending_tasks) - 5
            if remaining_pending > 0:
                lines.append(f"\n(You have {remaining_pending} other pending tasks from earlier)")

    elif status == "pending":
        lines.append(f"You have {len(pending_tasks)} pending tasks.\n")
        lines.append("The top 5 are:")
        for i, task in enumerate(pending_tasks[:5], start=1):
            title = task.get("title", "Untitled")
            lines.append(f"{i}. {title}")

        # Mention remaining tasks
        remaining_pending = len(pending_tasks) - 5
        if remaining_pending > 0:
            lines.append(f"\n(You have {remaining_pending} other pending tasks from earlier)")

    elif status == "completed":
        lines.append(f"You've completed {len(completed_tasks)} tasks!\n")
        lines.append("Here are your most recent:")
        for i, task in enumerate(completed_tasks[:5], start=1):
            title = task.get("title", "Untitled")
            lines.append(f"{i}. {title}")

        # Mention remaining completed tasks
        remaining_completed = len(completed_tasks) - 5
        if remaining_completed > 0:
            lines.append(f"\n(Plus {remaining_completed} other completed tasks)")

    return "\n".join(lines)




# ============================================================================
# MCP to OpenAI Adapter Layer (T032 Preview - Foundation for Tool Integration)
# ============================================================================

class MCPToolRegistry:
    """
    Centralized registry for MCP tools exposed to OpenAI agents.

    This class maintains a mapping of MCP tool names to their implementations
    and provides a clean interface for registering and retrieving tools.

    Design Rationale:
    - Separation of concerns: MCP tools remain independent of agent framework
    - Extensibility: New tools can be added without modifying agent code
    - Testability: Registry can be mocked for unit testing

    Usage:
        >>> registry = MCPToolRegistry()
        >>> registry.register_tool("add_task", ADD_TASK_SCHEMA, AddTaskTool())
        >>> tools = registry.list_tools()
    """

    def __init__(self):
        """Initialize the tool registry with empty tool map."""
        self._tools: Dict[str, Dict[str, Any]] = {}
        logger.info("MCPToolRegistry initialized")

    def register_tool(
        self,
        tool_name: str,
        mcp_schema: Dict[str, Any],
        mcp_tool_instance: Any
    ) -> None:
        """
        Register an MCP tool with its schema and implementation.

        Args:
            tool_name: Unique identifier for the tool (e.g., "add_task")
            mcp_schema: MCP tool schema dict with name, description, inputSchema
            mcp_tool_instance: Instance of the MCP tool class (e.g., AddTaskTool())

        Raises:
            ValueError: If tool_name is already registered

        Example:
            >>> registry = MCPToolRegistry()
            >>> registry.register_tool("add_task", ADD_TASK_SCHEMA, AddTaskTool())
        """
        if tool_name in self._tools:
            raise ValueError(f"Tool '{tool_name}' is already registered")

        self._tools[tool_name] = {
            "schema": mcp_schema,
            "instance": mcp_tool_instance
        }
        logger.info(f"Registered MCP tool: {tool_name}")

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve tool registration by name.

        Args:
            tool_name: Name of the tool to retrieve

        Returns:
            Dict with 'schema' and 'instance' keys, or None if not found

        Example:
            >>> tool = registry.get_tool("add_task")
            >>> instance = tool["instance"]
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """
        List names of all registered tools.

        Returns:
            List of tool names

        Example:
            >>> registry.list_tools()
            ['add_task', 'list_tasks', 'complete_task']
        """
        return list(self._tools.keys())


# ============================================================================
# Global Tool Registry Instance
# ============================================================================

# Create a singleton registry for the application
tool_registry = MCPToolRegistry()

# Register the add_task tool
tool_registry.register_tool("add_task", ADD_TASK_SCHEMA, AddTaskTool())

# Register the list_tasks tool (T041)
tool_registry.register_tool("list_tasks", LIST_TASKS_SCHEMA, ListTasksTool())


# ============================================================================
# Agent Setup with Tools
# ============================================================================

# Create function tool wrapper for add_task MCP tool
@function_tool
async def add_task_tool(
    ctx: RunContextWrapper[Dict[str, Any]],
    title: str,
    description: Optional[str] = None
) -> str:
    """
    Create a new task for the user.

    Use this tool when the user wants to add a new task to their todo list.
    The task will be associated with the user and can be managed through
    natural language commands.

    **When to use this tool:**
    - User says "Add a task to buy groceries"
    - User says "Create a reminder for my meeting"
    - User says "I need to remember to call John"
    - User says "Add todo: finish the report"

    Args:
        title: Task title (required, max 500 characters, must not be empty)
        description: Optional detailed task description (max 5000 characters)

    Returns:
        str: Result message describing the created task

    Examples:
        User says: "Add a task to buy groceries"
        Agent calls: add_task_tool(title="Buy groceries")

        User says: "Remind me to call the dentist tomorrow at 3pm"
        Agent calls: add_task_tool(title="Call dentist", description="Tomorrow at 3pm")
    """
    # Start timer for tool execution (T079)
    tool_start_time = time.time()

    # Log tool call with parameters (T079)
    logger.info(
        "Tool called: add_task",
        extra={
            "tool_name": "add_task",
            "user_id": ctx.context.get("user_id"),
            "title_length": len(title) if title else 0,
            "has_description": description is not None,
        }
    )

    try:
        # Extract user_id from context
        user_id = ctx.context.get("user_id")
        if not user_id:
            logger.error("user_id not found in agent context")
            return "Error: Could not identify user for task creation."

        # Call the MCP add_task function
        result = await add_task(
            user_id=str(user_id),
            title=title,
            description=description
        )

        # Calculate execution time (T079)
        duration_ms = (time.time() - tool_start_time) * 1000

        if result.get("success"):
            task_data = result.get("data", {})
            logger.info(
                f"Tool succeeded: add_task",
                extra={
                    "tool_name": "add_task",
                    "task_id": task_data.get('id'),
                    "user_id": user_id,
                    "title": task_data.get('title')[:100],  # Limit length in logs
                    "duration_ms": duration_ms,
                }
            )
            return (
                f"Task created successfully: {task_data.get('title')}"
            )
        else:
            logger.error(
                f"Tool failed: add_task",
                extra={
                    "tool_name": "add_task",
                    "user_id": user_id,
                    "error_message": result.get('message'),
                    "duration_ms": duration_ms,
                }
            )
            return f"Failed to create task: {result.get('message')}"

    except Exception as e:
        # Calculate execution time for failed call (T079)
        duration_ms = (time.time() - tool_start_time) * 1000

        logger.error(
            f"Tool error: add_task",
            exc_info=True,
            extra={
                "tool_name": "add_task",
                "user_id": ctx.context.get("user_id"),
                "error_type": e.__class__.__name__,
                "error_message": str(e),
                "duration_ms": duration_ms,
            }
        )
        return f"An error occurred while creating the task: {str(e)}"


# Create function tool wrapper for list_tasks MCP tool (T041)
@function_tool
async def list_tasks_tool(
    ctx: RunContextWrapper[Dict[str, Any]],
    status: str = "all"
) -> str:
    """
    List tasks for the user with optional status filtering.

    Use this tool when the user wants to see their tasks. You can filter
    tasks by completion status (pending, completed) or show all tasks.
    Tasks are always isolated to the authenticated user.

    **When to use this tool:**
    - User says "Show my tasks"
    - User says "What do I have to do?"
    - User says "What have I completed?"
    - User says "What's pending?"

    Args:
        status: Optional status filter - "all" (default), "pending", or "completed"

    Returns:
        str: Formatted task list with context-aware messages

    Examples:
        User says: "Show my tasks"
        Agent calls: list_tasks_tool(status="all")

        User says: "What's pending?"
        Agent calls: list_tasks_tool(status="pending")

        User says: "Show completed tasks"
        Agent calls: list_tasks_tool(status="completed")
    """
    # Start timer for tool execution (T079)
    tool_start_time = time.time()

    # Log tool call with parameters (T079)
    logger.info(
        "Tool called: list_tasks",
        extra={
            "tool_name": "list_tasks",
            "user_id": ctx.context.get("user_id"),
            "status_filter": status,
        }
    )

    try:
        # Extract user_id from context
        user_id = ctx.context.get("user_id")
        if not user_id:
            logger.error("user_id not found in agent context")
            return "Error: Could not identify user for task listing."

        # Call the MCP list_tasks function
        result = await list_tasks(
            user_id=str(user_id),
            status=status
        )

        # Calculate execution time (T079)
        duration_ms = (time.time() - tool_start_time) * 1000

        if result.get("success"):
            tasks_data = result.get("data", [])
            task_count = len(tasks_data)

            logger.info(
                f"Tool succeeded: list_tasks",
                extra={
                    "tool_name": "list_tasks",
                    "user_id": user_id,
                    "status_filter": status,
                    "task_count": task_count,
                    "duration_ms": duration_ms,
                }
            )

            # Format task list for conversational display (T042)
            formatted_list = format_task_list_for_display(tasks_data, status)
            return formatted_list
        else:
            logger.error(
                f"Tool failed: list_tasks",
                extra={
                    "tool_name": "list_tasks",
                    "user_id": user_id,
                    "status_filter": status,
                    "error_message": result.get('message'),
                    "duration_ms": duration_ms,
                }
            )
            return f"Failed to list tasks: {result.get('message')}"

    except Exception as e:
        # Calculate execution time for failed call (T079)
        duration_ms = (time.time() - tool_start_time) * 1000

        logger.error(
            f"Tool error: list_tasks",
            exc_info=True,
            extra={
                "tool_name": "list_tasks",
                "user_id": ctx.context.get("user_id"),
                "status_filter": status,
                "error_type": e.__class__.__name__,
                "error_message": str(e),
                "duration_ms": duration_ms,
            }
        )
        return f"An error occurred while listing tasks: {str(e)}"


# Create function tool wrapper for complete_task MCP tool (T049)
@function_tool
async def complete_task_tool(
    ctx: RunContextWrapper[Dict[str, Any]],
    task_id: int
) -> str:
    """
    Mark a task as completed for the user.

    Use this tool when the user wants to mark a task as done or completed.
    Validates task ownership before updating the completion status.

    **When to use this tool:**
    - User says "Mark task 3 as done"
    - User says "I finished buying groceries"
    - User says "Complete the dentist task"
    - User says "I'm done with the report"

    Args:
        task_id: Task's unique identifier (integer, minimum 1)

    Returns:
        str: Result message describing the completed task

    Examples:
        User says: "Mark task 3 as done"
        Agent calls: complete_task_tool(task_id=3)

        User says: "I finished buying groceries"
        Agent calls: list_tasks_tool(status="pending") to find task, then complete_task_tool(task_id=1)

    **Ambiguous Task References (T050):**
    - If user mentions a task title (not ID), first call list_tasks_tool(status="pending")
    - Match task titles against user's reference (case-insensitive substring match)
    - If exact match: proceed with complete_task_tool
    - If multiple matches: ask for clarification
      Example: "Which task? I found: 1. Buy groceries, 2. Buy groceries for party"
    - If no matches: inform user
      Example: "I couldn't find a task matching 'groceries'. Would you like to see your pending tasks?"
    """
    try:
        # Extract user_id from context
        user_id = ctx.context.get("user_id")
        if not user_id:
            logger.error("user_id not found in agent context")
            return "Error: Could not identify user for task completion."

        # Call the MCP complete_task function
        result = await complete_task(
            user_id=str(user_id),
            task_id=task_id
        )

        if result.get("success"):
            task_data = result.get("data", {}).get("task", {})
            logger.info(
                f"Task completed via agent: id={task_data.get('id')}, "
                f"title='{task_data.get('title', 'Unknown')[:50]}...', user_id={user_id}"
            )
            return (
                f"Great! I've marked task {task_data.get('id')} "
                f"({task_data.get('title', 'Unknown')}) as completed."
            )
        else:
            message = result.get("message", "Unknown error")
            logger.error(f"Task completion failed: {message}")

            # Handle ownership/not found errors with user-friendly messages
            if "not found" in message.lower():
                return "I couldn't find that task. Would you like to see your pending tasks?"
            return f"Failed to complete task: {message}"

    except Exception as e:
        logger.error(f"Error in complete_task_tool: {str(e)}", exc_info=True)
        return f"An error occurred while completing the task: {str(e)}"


# Create function tool wrapper for update_task MCP tool (T056)
@function_tool
async def update_task_tool(
    ctx: RunContextWrapper[Dict[str, Any]],
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    Update a task's title and/or description for the user.

    Use this tool when the user wants to modify, change, or update an existing task.
    At least one of title or description must be provided. Validates task ownership
    before updating.

    **When to use this tool:**
    - User says "Change the dentist task to Tuesday"
    - User says "Update task 2 title to Buy groceries"
    - User says "Modify the report task description"
    - User says "Edit task 5"

    Args:
        task_id: Task's unique identifier (integer, minimum 1)
        title: Optional new task title (max 500 characters)
        description: Optional new task description (max 5000 characters)

    Returns:
        str: Result message describing the updated task with change summary (T057)

    Examples:
        User says: "Change the dentist task to Tuesday"
        Agent calls: list_tasks_tool(status="all") to find task, then update_task_tool(task_id=2, description="Tuesday")

        User says: "Update task 3 title to Buy groceries"
        Agent calls: update_task_tool(task_id=3, title="Buy groceries")

    **Confirmation Response (T057):**
    - The tool tracks what changed and includes it in the response
    - Example: "I've updated task 2. Changed description to 'Tuesday'."
    - Example: "I've updated task 3. Changed title from 'Old' to 'Buy groceries'."
    - If no actual changes needed: "That task is already up to date."

    **Ambiguous Task References:**
    - If user mentions a task title (not ID), first call list_tasks_tool(status="all")
    - Match task titles against user's reference (case-insensitive substring match)
    - If exact match: proceed with update_task_tool
    - If multiple matches: ask for clarification
    - If no matches: inform user
    """
    try:
        # Extract user_id from context
        user_id = ctx.context.get("user_id")
        if not user_id:
            logger.error("user_id not found in agent context")
            return "Error: Could not identify user for task update."

        # Call the MCP update_task function
        result = await update_task(
            user_id=str(user_id),
            task_id=task_id,
            title=title,
            description=description
        )

        if result.get("success"):
            message = result.get("message", "")
            task_data = result.get("data", {}).get("task", {})
            logger.info(
                f"Task updated via agent: id={task_data.get('id')}, "
                f"title='{task_data.get('title', 'Unknown')[:50]}...', user_id={user_id}"
            )

            # Format confirmation response with change summary (T057)
            if "No changes needed" in message:
                return f"That task is already up to date. Title: {task_data.get('title', 'Unknown')}"
            return f"I've updated task {task_data.get('id')}. {message}"
        else:
            message = result.get("message", "Unknown error")
            logger.error(f"Task update failed: {message}")

            # Handle ownership/not found/validation errors with user-friendly messages
            if "not found" in message.lower():
                return "I couldn't find that task. Would you like to see your tasks?"
            if "at least one" in message.lower():
                return "I need at least a new title or description to update the task. What would you like to change?"
            return f"Failed to update task: {message}"

    except Exception as e:
        logger.error(f"Error in update_task_tool: {str(e)}", exc_info=True)
        return f"An error occurred while updating the task: {str(e)}"


# Create function tool wrapper for delete_task MCP tool (T063)
@function_tool
async def delete_task_tool(
    ctx: RunContextWrapper[Dict[str, Any]],
    task_id: int
) -> str:
    """
    Delete a task for the user.

    Use this tool when the user wants to permanently remove a task.
    Validates task ownership before performing deletion. Deletion cannot be undone.

    **When to use this tool:**
    - User says "Delete the grocery task"
    - User says "Remove task 4"
    - User says "Get rid of the dentist task"
    - User says "I don't need task 2 anymore"

    Args:
        task_id: Task's unique identifier (integer, minimum 1)

    Returns:
        str: Confirmation message describing the deleted task (T064)

    Examples:
        User says: "Delete task 3"
        Agent calls: delete_task_tool(task_id=3)

        User says: "Remove the grocery task"
        Agent calls: list_tasks_tool(status="all") to find task, then delete_task_tool(task_id=1)

    **Confirmation Response (T064):**
    - Always confirm what was deleted: "I've deleted 'Buy groceries'."
    - Include task status if relevant: "I've deleted 'Buy groceries'. It was pending."
    - If uncertain, ask first: "Are you sure you want to delete 'Buy groceries'? This cannot be undone."
    """
    try:
        # Extract user_id from context
        user_id = ctx.context.get("user_id")
        if not user_id:
            logger.error("user_id not found in agent context")
            return "Error: Could not identify user for task deletion."

        # Call the MCP delete_task function
        result = await delete_task(
            user_id=str(user_id),
            task_id=task_id
        )

        if result.get("success"):
            task_data = result.get("data", {}).get("task", {})
            logger.info(
                f"Task deleted via agent: id={task_data.get('id')}, "
                f"title='{task_data.get('title', 'Unknown')[:50]}...', user_id={user_id}"
            )

            # Format confirmation response (T064)
            title = task_data.get('title', 'Unknown')
            status = "completed" if task_data.get('completed') else "pending"
            return f"I've deleted '{title}'. It was marked as {status}."
        else:
            message = result.get("message", "Unknown error")
            logger.error(f"Task deletion failed: {message}")

            # Handle ownership/not found errors with user-friendly messages
            if "not found" in message.lower():
                return "I couldn't find that task. Would you like to see your tasks?"
            return f"Failed to delete task: {message}"

    except Exception as e:
        logger.error(f"Error in delete_task_tool: {str(e)}", exc_info=True)
        return f"An error occurred while deleting the task: {str(e)}"


# Create the primary agent instance
def create_todo_agent() -> AgentBase:
    """
    Create and configure the Todo AI Chatbot agent.

    Initializes the agent with:
    - Comprehensive instructions for task creation intent interpretation (T030)
    - Tools for task operations (add_task, list_tasks)
    - Default model configuration with temperature=0 for deterministic responses

    Agent Configuration Details:
    - Model: gpt-4o-mini (fast, cost-effective, optimized for function calling)
    - Temperature: 0.0 (deterministic, consistent tool selection)
    - Max Tokens: 500 (concise responses)
    - Tool Use: Enabled with add_task_tool and list_tasks_tool (T041)

    Returns:
        AgentBase: Configured agent instance ready for execution

    Example:
        >>> agent = create_todo_agent()
        >>> result = await execute_agent(user_id, [], "Add a task to buy groceries")
    """
    agent = Agent(
        name="TodoAssistant",
        instructions=AGENT_INSTRUCTIONS,
        tools=[add_task_tool, list_tasks_tool, complete_task_tool, update_task_tool, delete_task_tool],
    )

    logger.info(
        "Todo agent created with add_task, list_tasks, complete_task, update_task, and delete_task tools (T063), "
        f"model={DEFAULT_MODEL}, temperature={AGENT_TEMPERATURE}"
    )
    return agent


# Global agent instance (reused across requests for efficiency)
_todo_agent: Optional[AgentBase] = None


def get_todo_agent() -> AgentBase:
    """
    Get or create the global todo agent instance.

    Uses singleton pattern to avoid recreating the agent on every request.
    The agent is stateless and safe to reuse across different user contexts.

    Returns:
        AgentBase: The todo agent instance

    Example:
        >>> agent = get_todo_agent()
        >>> result = await Runner.run(agent, "Hello")
    """
    global _todo_agent
    if _todo_agent is None:
        _todo_agent = create_todo_agent()
    return _todo_agent


# ============================================================================
# Agent Execution Function (T031 Placeholder)
# ============================================================================

async def execute_agent(
    user_id: UUID,
    conversation_history: List[Message],
    message: str
) -> Dict[str, Any]:
    """
    Execute the AI agent with conversation context and new user message.

    This is the core agent execution function that:
    1. Formats conversation history for the OpenAI Agents SDK
    2. Creates agent context with user_id for data isolation
    3. Executes the agent with the current message and conversation history
    4. Processes any tool calls made by the agent (e.g., add_task)
    5. Returns structured response with assistant message and tool results

    The function handles:
    - Conversation context loading and formatting
    - Agent execution with proper error handling
    - Tool invocation and result processing
    - Timeout management
    - Comprehensive logging for debugging (T079)

    Args:
        user_id: Authenticated user's UUID (from JWT token)
        conversation_history: List of Message objects from database (ordered chronologically)
        message: Current user message to process

    Returns:
        Dict with execution results:
        {
            "success": True,  # Whether execution succeeded
            "assistant_message": "The agent's text response to the user",
            "tool_calls": [  # List of tool calls made during execution
                {
                    "tool_name": "add_task",
                    "arguments": {"title": "Buy groceries", "description": null},
                    "result": "Task created successfully: Buy groceries"
                }
            ],
            "raw_response": {...},  # Full RunResult object for debugging
            "error": None  # Error message if execution failed
        }

    Raises:
        ValueError: If message is empty or invalid
        RuntimeError: If agent execution fails after retries
        asyncio.TimeoutError: If agent execution exceeds timeout

    Example:
        >>> messages = await fetch_conversation_history(session, conversation_id)
        >>> result = await execute_agent(user_id, messages, "Add a task to buy milk")
        >>> print(result["assistant_message"])
        "I've created a task called 'Buy groceries' for you."
        >>> print(result["tool_calls"][0]["result"])
        "Task created successfully: Buy groceries"

    Note:
        - Conversation history is truncated to MAX_CONTEXT_TOKENS to prevent context overflow
        - Tool calls are executed in the agent's run loop automatically
        - User context is passed to tools for data isolation
        - All database operations are scoped by user_id
        - Comprehensive execution logging is implemented (T079)
    """
    # Start timer for agent execution (T079)
    execution_start_time = time.time()

    # Log agent execution start (T079)
    logger.info(
        "Agent execution started",
        extra={
            "user_id": str(user_id),
            "conversation_history_length": len(conversation_history),
            "message_length": len(message),
            "message_preview": message[:100],  # First 100 chars
        }
    )

    # Validate input
    if not message or not message.strip():
        logger.error("execute_agent called with empty message")
        raise ValueError("Message cannot be empty")

    try:
        # Step 1: Format conversation history for OpenAI Agents SDK
        formatted_history = format_messages_for_agent(conversation_history)
        logger.debug(f"Formatted {len(formatted_history)} messages for agent input")

        # Step 2: Truncate history to fit within context window
        truncated_history = truncate_history_to_max(
            formatted_history,
            max_tokens=MAX_CONTEXT_TOKENS
        )
        if len(truncated_history) < len(formatted_history):
            logger.info(
                f"Truncated conversation history from {len(formatted_history)} "
                f"to {len(truncated_history)} messages to fit context window"
            )

        # Step 3: Create agent context with user_id
        # This context is passed to tools for data isolation
        agent_context = {
            "user_id": str(user_id)
        }
        context_wrapper = RunContextWrapper(context=agent_context)

        # Step 4: Get agent instance
        agent = get_todo_agent()
        logger.debug("Retrieved todo agent instance")

        # Step 5: Build conversation input for agent
        # Combine history with current message
        conversation_input = []

        # Add conversation history (if any)
        for msg in truncated_history:
            conversation_input.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Add current user message
        conversation_input.append({
            "role": "user",
            "content": message
        })

        logger.debug(f"Agent input prepared with {len(conversation_input)} total messages")

        # Step 6: Execute agent with timeout protection
        try:
            logger.info(f"Running agent with {len(conversation_input)} messages")
            agent_run_start = time.time()
            run_result = await asyncio.wait_for(
                Runner.run(
                    agent,
                    input=conversation_input,
                    context=context_wrapper,
                ),
                timeout=AGENT_TIMEOUT
            )
            agent_run_duration_ms = (time.time() - agent_run_start) * 1000

            logger.info(
                f"Agent run completed",
                extra={
                    "user_id": str(user_id),
                    "total_requests": run_result.usage.total_requests,
                    "agent_run_duration_ms": agent_run_duration_ms,
                }
            )

        except asyncio.TimeoutError:
            # Calculate duration before timeout (T079)
            duration_ms = (time.time() - agent_run_start) * 1000

            logger.error(
                f"Agent execution exceeded timeout",
                extra={
                    "user_id": str(user_id),
                    "timeout_seconds": AGENT_TIMEOUT,
                    "duration_ms": duration_ms,
                }
            )
            raise RuntimeError(
                f"Agent execution timed out after {AGENT_TIMEOUT} seconds. "
                "The request took too long to process."
            )

        # Step 7: Extract tool calls from result
        tool_calls = []
        # Iterate through new items to find tool calls
        for item in run_result.new_items:
            # Check if item is a tool call (tool calls in Agents SDK appear as specific types)
            if hasattr(item, 'tool_name'):
                tool_call_info = {
                    "tool_name": item.tool_name,
                    "arguments": getattr(item, 'arguments', {}),
                    "result": getattr(item, 'output', None)
                }
                tool_calls.append(tool_call_info)

                # Log tool call with result (T079)
                logger.info(
                    f"Tool call executed: {item.tool_name}",
                    extra={
                        "tool_name": item.tool_name,
                        "has_arguments": bool(getattr(item, 'arguments', {})),
                        "result_preview": str(getattr(item, 'output', ''))[:100],
                    }
                )

        # Step 8: Extract final assistant message
        assistant_message = run_result.final_output
        if not assistant_message:
            logger.warning("Agent returned empty final_output, using fallback")
            assistant_message = "I'm sorry, I couldn't generate a response. Please try again."

        # Calculate total execution time (T079)
        total_duration_ms = (time.time() - execution_start_time) * 1000

        # Log successful execution summary (T079)
        logger.info(
            "Agent execution completed successfully",
            extra={
                "user_id": str(user_id),
                "assistant_response_length": len(assistant_message),
                "tool_calls_count": len(tool_calls),
                "total_duration_ms": total_duration_ms,
                "tool_names": [tc["tool_name"] for tc in tool_calls],
            }
        )

        # Step 9: Return structured response
        return {
            "success": True,
            "assistant_message": assistant_message,
            "tool_calls": tool_calls,
            "raw_response": run_result,
            "error": None
        }

    except ValueError as e:
        # Re-raise validation errors (empty message, etc.)
        duration_ms = (time.time() - execution_start_time) * 1000
        logger.error(
            f"Validation error in execute_agent",
            extra={
                "user_id": str(user_id),
                "error_type": "ValueError",
                "error_message": str(e),
                "duration_ms": duration_ms,
            }
        )
        raise

    except asyncio.TimeoutError as e:
        # Timeout errors
        duration_ms = (time.time() - execution_start_time) * 1000
        logger.error(
            f"Timeout error in execute_agent",
            extra={
                "user_id": str(user_id),
                "error_type": "TimeoutError",
                "timeout_seconds": AGENT_TIMEOUT,
                "duration_ms": duration_ms,
            }
        )
        return {
            "success": False,
            "assistant_message": (
                "I'm sorry, processing your request took too long. "
                "Please try again with a shorter request."
            ),
            "tool_calls": [],
            "raw_response": None,
            "error": "AGENT_TIMEOUT"
        }

    except Exception as e:
        # Unexpected errors
        duration_ms = (time.time() - execution_start_time) * 1000
        logger.error(
            f"Unexpected error in execute_agent",
            exc_info=True,
            extra={
                "user_id": str(user_id),
                "error_type": e.__class__.__name__,
                "error_message": str(e),
                "duration_ms": duration_ms,
            }
        )
        return {
            "success": False,
            "assistant_message": (
                "I'm sorry, I encountered an error while processing your request. "
                "Please try again later."
            ),
            "tool_calls": [],
            "raw_response": None,
            "error": str(e)
        }


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Core agent functions
    "execute_agent",
    "create_todo_agent",
    "get_todo_agent",
    "add_task_tool",
    "list_tasks_tool",  # T041

    # Task list formatting (T042 & T043)
    "format_task_list_for_display",

    # Configuration constants
    "DEFAULT_MODEL",
    "AGENT_TIMEOUT",
    "MAX_CONTEXT_TOKENS",
    "AGENT_TEMPERATURE",
    "MAX_TOKENS",

    # System instructions (T030)
    "AGENT_INSTRUCTIONS",

    # MCP to OpenAI adapter (T032 foundation)
    "MCPToolRegistry",
    "tool_registry",
]
