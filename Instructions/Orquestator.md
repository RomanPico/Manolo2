# Orchestrator

## Purpose

The orchestrator is the component that coordinates one assistant run from user input to final answer.

Its job is to control the execution flow, not to implement storage, tool internals, or provider-specific LLM logic.

---

## Responsibilities

The orchestrator should:

- receive a new user request
- start and track a run
- build the active context for the current iteration
- call the LLM
- inspect the LLM response
- decide whether the run is finished or must continue
- validate and route tool calls to the tool executor
- append tool results back into the loop
- enforce execution policies
- finalize the run with a final answer or controlled failure

---

## What it should contain

The orchestrator should contain the following concerns.

### 1. Run control
It must own the lifecycle of a run.

This includes:

- run start
- run status
- current step
- loop termination
- finalization

### 2. Loop control
It must control the main execution loop.

Typical loop:

1. build context
2. call LLM
3. inspect output
4. if final answer -> finish
5. if tool call -> execute tool and continue
6. stop if limits are reached

### 3. Context coordination
It must decide what goes into the prompt or model input at each step.

Examples:

- user message
- recent conversation history
- system instructions
- tool definitions
- prior tool results

It does not need to implement retrieval internally, but it must decide when and how that context is assembled.

### 4. Policy enforcement
It must enforce global execution rules such as:

- maximum number of steps
- maximum number of tool calls
- allowed tools
- blocked tools
- read-only vs write tools
- fallback behavior

### 5. Error handling
It must define what to do when something fails.

Examples:

- invalid tool call
- tool execution failure
- model failure
- context build failure
- step limit reached

### 6. Final decision point
It must determine whether the run:

- completed successfully
- should continue
- should stop with fallback
- failed

---

## What it should NOT contain

The orchestrator should **not** contain:

- raw SQL queries
- SQLite implementation details
- provider-specific HTTP logic
- tool business logic
- embedding or retrieval internals
- frontend code
- logging backend implementation

If those things end up inside the orchestrator, it becomes too coupled and hard to grow.

---

## Internal design

## Main state

The orchestrator should keep an explicit execution state.

```python id="c5a0cr"
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class OrchestrationState:
    run_id: str
    conversation_id: str
    user_message: str
    messages: list[dict] = field(default_factory=list)
    step_count: int = 0
    max_steps: int = 5
    tool_calls_made: int = 0
    status: str = "running"
    final_answer: Optional[str] = None
    last_error: Optional[str] = None