"""
Agent Service for Todo AI Chatbot.

This service handles AI agent interactions using OpenAI API with function calling.
It processes user messages with conversation history and invokes MCP tools as needed.
"""
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# System prompt for the AI agent
# Optimized for token usage (T101) - reduced from ~350 to ~180 tokens
SYSTEM_PROMPT = """You are a task management assistant. Help users manage tasks using these tools:

1. add_task(title, description?) - Create task
2. list_tasks(status?) - List tasks (all/pending/completed)
3. complete_task(task_id) - Mark task done
4. update_task(task_id, title?, description?) - Modify task
5. delete_task(task_id) - Remove task

Rules:
- Be friendly and conversational
- Extract intent from natural language
- Confirm successful actions
- Ask if ambiguous (e.g., "which task?")
- Maintain conversation context
- Be concise

Examples:
- "Add task buy groceries" → add_task → "Added 'Buy groceries'"
- "What's pending?" → list_tasks(status="pending") → [list]
- "Mark task 1 done" → complete_task(1) → "Task 1 completed"
"""


async def process_message(
    user_id: str,
    conversation_history: List[Dict[str, Any]],
    new_message: str
) -> Dict[str, Any]:
    """
    Process a user message with conversation history and return AI response.

    This function:
    1. Formats conversation history for OpenAI API
    2. Calls OpenAI chat completions with function calling
    3. Invokes MCP tools if the agent decides to use them
    4. Returns the agent's response with any tool calls made

    Args:
        user_id: User UUID for tool invocations
        conversation_history: List of previous messages with role and content
            Example: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        new_message: The new user message to process

    Returns:
        Dict with agent response and tool calls:
        {
            "response": "I've added 'Buy groceries' to your tasks.",
            "tool_calls": [
                {
                    "tool_name": "add_task",
                    "parameters": {"title": "Buy groceries"},
                    "result": {"success": True, "data": {...}}
                }
            ]
        }
    """
    try:
        # Format conversation history for OpenAI API
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history (limit to last 20 messages to stay within token limits)
        for msg in conversation_history[-20:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Add new message
        messages.append({
            "role": "user",
            "content": new_message
        })

        # Define function calling schemas for MCP tools
        functions = [
            {
                "name": "add_task",
                "description": "Create a new task with a title and optional description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User UUID from JWT token"
                        },
                        "title": {
                            "type": "string",
                            "description": "Task title (1-200 characters)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional task description (max 1000 characters)"
                        }
                    },
                    "required": ["user_id", "title"]
                }
            },
            {
                "name": "list_tasks",
                "description": "List all tasks or filter by completion status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User UUID from JWT token"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["all", "pending", "completed"],
                            "description": "Filter by status"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "complete_task",
                "description": "Mark a task as completed",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User UUID from JWT token"
                        },
                        "task_id": {
                            "type": "integer",
                            "description": "Task ID to mark as completed"
                        }
                    },
                    "required": ["user_id", "task_id"]
                }
            },
            {
                "name": "update_task",
                "description": "Update a task's title and/or description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User UUID from JWT token"
                        },
                        "task_id": {
                            "type": "integer",
                            "description": "Task ID to update"
                        },
                        "title": {
                            "type": "string",
                            "description": "New task title (1-200 characters)"
                        },
                        "description": {
                            "type": "string",
                            "description": "New task description (max 1000 characters)"
                        }
                    },
                    "required": ["user_id", "task_id"]
                }
            },
            {
                "name": "delete_task",
                "description": "Delete a task permanently",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User UUID from JWT token"
                        },
                        "task_id": {
                            "type": "integer",
                            "description": "Task ID to delete"
                        }
                    },
                    "required": ["user_id", "task_id"]
                }
            }
        ]

        # Call OpenAI API
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            functions=functions,
            function_call="auto",  # Let the model decide whether to call functions
            temperature=0.7,
            max_tokens=500
        )

        # Get the assistant's message
        assistant_message = response.choices[0].message

        # Check if the agent wants to call any tools
        tool_calls = []

        if assistant_message.function_call:
            # Single tool call
            function_name = assistant_message.function_call.name
            function_args = eval(assistant_message.function_call.arguments)  # Parse JSON string

            # Inject user_id into parameters
            function_args["user_id"] = user_id

            # Import and call the appropriate MCP tool
            from src.mcp_tools import add_task, list_tasks, complete_task, update_task, delete_task

            tool_map = {
                "add_task": add_task,
                "list_tasks": list_tasks,
                "complete_task": complete_task,
                "update_task": update_task,
                "delete_task": delete_task
            }

            tool_func = tool_map.get(function_name)
            if tool_func:
                # Call the tool
                result = await tool_func(**function_args)

                tool_calls.append({
                    "tool_name": function_name,
                    "parameters": function_args,
                    "result": result
                })

                # Generate a follow-up response acknowledging the tool result
                if result.get("success"):
                    messages.append(assistant_message)  # Assistant's function call message
                    messages.append({
                        "role": "function",
                        "name": function_name,
                        "content": str(result)
                    })

                    # Get final response from agent
                    final_response = client.chat.completions.create(
                        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                        messages=messages,
                        temperature=0.7,
                        max_tokens=500
                    )

                    response_text = final_response.choices[0].message.content
                else:
                    response_text = f"Sorry, I couldn't complete that action. {result.get('message', 'Unknown error')}"
            else:
                response_text = "Sorry, I encountered an error processing your request."
        else:
            # No tool calls, just a text response
            response_text = assistant_message.content
            tool_calls = []

        return {
            "response": response_text,
            "tool_calls": tool_calls
        }

    except Exception as e:
        # Return error response
        return {
            "response": f"Sorry, I encountered an error: {str(e)}",
            "tool_calls": []
        }
