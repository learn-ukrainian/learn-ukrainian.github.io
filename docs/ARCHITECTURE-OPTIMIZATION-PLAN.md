# Architecture Optimization Plan

**Status:** Proposed
**Date:** 2026-02-11
**Objective:** Optimize system performance, resource utilization, and agent collaboration.

## 1. WebUI-Backend Sync

**Goal:** Transform the static/polling-based UI into a reactive, real-time control center.

### Proposed Actions
*   **Implement RESTful API standards.**
*   **Define clear data contracts (JSON Schema).**
*   **Establish real-time sync (WebSockets/SSE).**
*   **Optimize backend logic for performance.**
*   **Implement asynchronous processing.**

### Implementation Details
*   **API Standards:** Adopt OpenAPI (Swagger) for API definition and documentation.
*   **Data Contracts:** Utilize JSON Schema validation for all API request/response payloads.
*   **Real-time Sync:** Implement Socket.IO for bidirectional communication, falling back to SSE for read-only updates.
*   **Backend Logic:** Profile critical endpoints; refactor bottlenecks using worker queues (e.g., Redis Queue, Celery).
*   **Async Processing:** Employ `async/await` patterns in backend services; utilize message queues for long-running tasks.

## 2. Agent Communication Optimization

**Goal:** Eliminate redundant communication, reduce resource waste (tokens/compute), and enforce strict role separation.

### Proposed Actions
*   **Consolidate Agent Roles:** Define distinct responsibilities for Gemini (content generation) and Claude (architecture, orchestration).
*   **Event-Driven Architecture:** Transition from direct calls to an event bus for inter-agent communication.
*   **Task Prioritization:** Implement a queuing system with dynamic prioritization based on project goals.
*   **Resource Monitoring:** Track agent activity and resource utilization to identify and eliminate waste.
*   **Automated Handoffs:** Develop triggers for automatic task reassignment based on agent availability and expertise.
*   **Data Serialization:** Standardize data formats (e.g., Protobuf, Avro) for efficient inter-agent data transfer.
*   **Caching Layer:** Implement caching for frequently accessed data and computation results.
*   **Batch Processing:** Group related tasks for efficient processing.
*   **State Management:** Centralize state management to avoid redundant computations and ensure consistency.
*   **Error Handling & Retries:** Implement robust error handling and retry mechanisms for inter-agent communication.
*   **Performance Metrics:** Define and track key performance indicators (KPIs) for agent communication efficiency.
*   **Resource Allocation:** Dynamically allocate resources based on task demand.
*   **Decommission Redundant Communication:** Identify and eliminate communication channels that do not align with defined roles or add value.
*   **Define Clear SLAs:** Establish Service Level Agreements for inter-agent communication response times and reliability.
*   **Feedback Loop:** Implement a mechanism for agents to provide feedback on communication efficiency.

### Implementation Details
*   **Consolidated Roles:**
    *   **Gemini:** Content generation (modules, vocabulary), initial audits, research.
    *   **Claude:** Architecture decisions, complex refactoring, code generation, pipeline orchestration.
*   **Event Bus:** Utilize a message broker (e.g., RabbitMQ, Kafka or lightweight SQLite event loop) for asynchronous, decoupled communication. Define strict event schemas.
*   **Task Prioritization:** Implement priority levels (`critical`, `high`, `medium`, `low`) in task messages. Use weighted queues.
*   **Resource Monitoring:** Integrate monitoring for real-time metrics on CPU, memory, and token usage per agent. Log agent activity timestamps and task durations.
*   **Automated Handoffs:** Trigger reassignment if agent A times out on task X; re-queue task X for agent B based on expertise mapping.
*   **Data Serialization:** Use structured formats (JSON/Protobuf) for inter-agent messages.
*   **Caching Layer:** Implement caching (Redis or file-based) for module metadata, vocabulary, and research findings to prevent re-generation.
*   **Batch Processing:** Group module audits, vocabulary enrichment, or content generation requests into batches to minimize context switching.
*   **State Management:** Centralize task state in a database (e.g., PostgreSQL or SQLite) accessible by all agents.
*   **Error Handling:** Implement exponential backoff for retries. Define dead-letter queues for unrecoverable errors.
*   **Performance Metrics:** Track `avg_task_completion_time`, `agent_throughput`, `communication_latency`.
*   **Decommission Redundant Comm:** **IMMEDIATE ACTION:** Remove direct Gemini->Claude escalation calls for routine batch failures. Transition to event bus or manual flags.
*   **SLAs:** Define response times (e.g., Gemini content: 1hr/module). Reliability: 99.9% uptime for event bus.
*   **Feedback Loop:** Agents post `communication_feedback` events to the bus detailing latency, errors, or clarity issues.
