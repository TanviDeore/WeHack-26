# WeHack-26

# Inspiration
Most agents operate in the moment, lacking the ability to truly learn from history, adapt over time, or explain their decisions. In industries like commercial real estate and infrastructure management, this limitation is costly. We were inspired by two ideas:

**CBRE’s challenge**: transforming massive streams of operational data into durable, actionable memory
"Night at the Museum” theme: bringing the past to life; not as static records, but as active intelligence that shapes the future. The organizations often struggle to connect these stages, planning is static, operations are reactive, and maintenance is delayed.

# What it does
CenterMind AI provides an hybrid-memory multi-agent platform with three main components:

i. Real-Time Operations Module - Detects present anomalies and resolves them using historical data

Monitors live metrics like temperature, load, and power usage.
Detects anomalies and triggers alerts.
Suggests actions based on historical patterns.

ii. Predictive Maintenance Module - Simulates future scenarios and predicts failures before they happen.

Uses historical data to predict potential failures.
Recommends preventive actions before incidents occur.
Reduces downtime and operational risks.

iii. Planning Module - Recommends optimal expansion strategies using historical data.

Suggests optimal data center locations.
Considers factors like power availability, cooling, budget, and capacity needs.
Ranks locations based on risk scores.
How we built it
We designed a hybrid memory system and agent framework.

# Memory Architecture

i. Long-Term Memory (Neo4j GraphDB) - Structured, queryable knowledge graph storing:

- Historical incidents
- System relationships
- Regional performance metrics

ii. Short-Term Memory (Redis) - High-speed ingestion of live telemetry:

- Temperature, CPU load, network gbps, fan speed, latency, power usage.
- Real-time system states
- Combines retrieval from graph memory with LLM reasoning for context-aware decisions

*Agent Orchestration*

- LangGraph: Multi-agent workflows and decision trees
- Gemini 2.5 Flash: Fast, multimodal reasoning engine

*Backend* - FastAPI

*Frontend* - React + Vite

# Challenges we ran into

- It was a challenge to decide which data is relevant to be stored in the long-term memory.
- Implementation of reward modeling became a challenge as the model became too biased towards the location preferences given by the user.

# Accomplishments that we're proud of
- Three distinct agents (Planning, Insights, Operations) with defined roles that communicate through hybrid memory (shared knowledge) combining Redis (real-time) and Neo4j (historical).
- Users can test scenarios with different priorities/budgets/states and instantly see recommendations on a visual map with comparison tables, turning complex infrastructure analysis into simple choices
- Operations Agent continuously monitors datacenters, detects anomalies, auto-diagnoses against historical patterns, and renders live chart visualizations with metrics (Temperature, CPU load, Network bandwidth) that update every 3 seconds based on real-time data pulled from the Redis memory.
- Every recommendation, alert, and action is backed by evidence from the Neo4j graph and Redis stream that makes it context-aware to avoid hallucinations
- Human-in-the-loop feedback loop - Operations Agent recommends corrective actions for incidents; users approve or reject each action; approved actions are automatically updated in Neo4j database, enabling the system to learn from operator decisions
- Predictive Maintenance agent analyzes datacenter performance and displays potential failure risks; users can interactively adjust operational parameters on sliders to see how Productivity Score changes, for a "what-if" scenario testing to optimize performance before failures occur.

# What we learned
- Memory is the missing layer in AI systems. Intelligence isn’t just reasoning, it’s remembering and evolving.
- Graph-based memory unlocks relationships that traditional storage cannot.
- Collaboration only works when agents operate on a unified memory layer.

# What's next for CenterMind AI

- Currently focused on a single client, scale the product to be used by multiple clients.
- We are currently focused in USA, making it available for others countries as well.
- Currently our application focuses just on data centers, we will expand it to all types of real estate.
