# Horizon

**Career intelligence platform. Not a job board. Not a chatbot.**

**[Live demo](https://horizon-six-beryl.vercel.app/)**

Horizon builds career roadmaps grounded in real job descriptions, real interview signals, and a graph that gets sharper with every request. The system's prior knowledge compounds across users & each run makes the next one better.

---

## Why

Career advice is generic or expensive, and neither reflects what's actually being hired for right now. Most AI career tools ignore the real hiring bar and cite nothing.

Horizon works differently: real evidence (live JDs, Blind posts, engineering blogs) constrains the LLM rather than replacing it, and what gets learned gets persisted into a graph that future requests query first.

---

## Career Tree (`tree.py`)

The flagship. Builds a 5-path career roadmap, 4+ stages each, every claim sourced from real web evidence.

```
Skills -> Neo4j Traversal -> Parallel Evidence Fetch -> Gemini Synthesis -> Citation Resolution -> Graph Evolution
```

**Graph-first.** Before any LLM call, Horizon queries Neo4j for validated trajectories. It finds roles by weighted skill overlap (`REQUIRES` edges), then walks `TRANSITIONS_TO` edges up to 15 hops to a terminal role. LLM is the cold-start fallback. As the graph matures, those calls become rarer.

**Parallel evidence fetch.** For each archetype, Tavily runs advanced searches constrained to high-signal domains (Blind, HN, Reddit, FAANG engineering blogs, LinkedIn). Up to 14 sources per archetype, fetched in parallel via `asyncio.gather`, tagged `SOURCE_REF_N` and injected into the synthesis prompt.

**Grounded synthesis.** Gemini 2.5 Flash generates the full `CareerTree` JSON under hard constraints: every stage must cite 3+ sources, `fit_score` is a cold probability not a confidence boost, `eta_months` is pulled from evidence patterns, `observed_paths` extracts actual career sequences from the scraped results.

**Graph evolution.** After synthesis, `observed_paths` (e.g. `["SWE II", "Senior SWE", "Staff SWE"]`) are written back to Neo4j as `TRANSITIONS_TO` edges. More users, denser graph, better priors, better trees.

Trees cached in Redis for 24h (`horizon:tree:v7:{user_id}`).

---

## Company Advisory Cards (`discover.py`)

Target role + companies in, structured fit cards out, generated in parallel.

Two separate signal sources per company: Tavily pulls raw interview signals from Blind, Reddit, and HN (7-min cache); a separate Gemini web-grounded call extracts hard technical skills from live Greenhouse/Lever JDs (30-min cache). Both feed the final synthesis prompt.

Gemini scores against a strict rubric:

```
A (90-100): >80% stack match + production proof in target ecosystem
B (75-89):  >50% match, bridgeable via sibling tech
C (60-74):  <50% match, paradigm shift required, 3+ month ramp
D (<60):    Core engineering pillars missing

Modifiers: FAANG/unicorn exp -> +5pts | level mismatch -> cap 20 | ecosystem lock-in -> cap 30
```

Each `AdvisoryCard`: fit score, hiring bar difficulty, top 10 skill gaps strictly absent from the user's stack, a brutal sub-10-word verdict, 3-4 concrete next steps with named tech, one highest-signal advisory.

Every fresh JD fetch triggers `graph.evolve(role, skills)`, incrementing `REQUIRES` edge weights in Neo4j.

---

## The Graph (`neo_graph.py`)

Not a static knowledge base. Two live signal streams:

**From the discover pipeline:** every JD cache miss writes extracted skills as weighted `REQUIRES` edges:
```cypher
MERGE (r)-[e:REQUIRES]->(s)
  ON CREATE SET e.weight = 1.0, e.count = 1
  ON MATCH  SET e.count = e.count + 1, e.weight = e.weight + 0.1
```

**From tree synthesis:** observed career progressions ingested as `TRANSITIONS_TO` edges:
```cypher
MERGE (r1)-[t:TRANSITIONS_TO]->(r2)
  ON MATCH SET t.count = t.count + 1
```

Trajectory traversal walks `TRANSITIONS_TO` up to 15 hops, using weighted skill overlap to anchor the start role.

---

## Onboarding (`onboarding/`)

PDF ingested via PyMuPDF, converted to Markdown, parsed by Gemini into a structured schema (education, skills, projects). Skills canonicalized immediately through a synonym normalizer (`"ReactJS"` -> `"React"`).

MBTI questionnaire samples per-dimension questions from MongoDB, scores via Likert scaling, stores the personality type to weight path preferences downstream.

---

## Architecture

```
                    +---------------------------------+
                    |        FastAPI Backend          |
                    |      (fully async, uvicorn)     |
                    +----------+-------------+--------+
                               |             |
              +----------------v--+      +---v-----------------+
              |   Career Tree     |      |  Advisory Cards     |
              |   tree.py         |      |  discover.py        |
              +------+------------+      +----------+----------+
                     |                             |
         +-----------v-----------------------------v----------+
         |                   neo_graph.py                    |
         |  Neo4j | REQUIRES edges | TRANSITIONS_TO edges    |
         |  Graph-first retrieval | Continuous evolution     |
         +-----------------------------------------------------------+
                     |                             |
         +-----------v------+      +--------------v---------+
         |  Tavily Search   |      |   Gemini 2.5 Flash     |
         |  (multi-key)     |      |   (structured output)  |
         +------------------+      +------------------------+
                     |
         +-----------v-------------------------------------------+
         |               Redis (aioredis)                        |
         |   Tree 24h  |  Intel 7min  |  JD 30min               |
         +-------------------------------------------------------+
                     |
         +-----------v-------------------------------------------+
         |             MongoDB (Motor async)                     |
         |       User profiles  |  MBTI questions               |
         +-------------------------------------------------------+
```

---

## Design Notes

**Intelligence is distributed, not prompt-dependent.** The graph holds structural, persistent knowledge: role-to-skill weights and role-to-role transition priors that strengthen over time. The web intel layer (Blind, HN, Reddit, engineering blogs, live JDs) contributes the live, sourced signal that no static training set can match. The LLM synthesizes across both. None of the three is sufficient alone.

**Structured output throughout.** Every Gemini call is bound to a Pydantic schema. No regex fallbacks, no ambiguous parsing at any layer.

**Cache tiered by volatility.** Tree (24h), market intel, JDs. Each layer invalidated independently.

**Cost observability.** Every LLM call logs token counts and cost with per-operation labels (`fetch_jd`, `build_card`, `synthesize_tree`). Built to know what each request actually costs.

**Fully async.** FastAPI + Motor + aioredis + `asyncio.gather` throughout. Blocking I/O in `asyncio.to_thread`. The event loop never blocks.

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI, Uvicorn |
| AI | Gemini 2.5 Flash |
| Web Evidence | Tavily (advanced, multi-key) |
| Graph DB | Neo4j (async driver) |
| Primary DB | MongoDB (Motor async) |
| Cache | Redis (aioredis) |
| Resume Parsing | PyMuPDF, pymupdf4llm |
| Auth | JWT HS256 + bcrypt |
| Validation | Pydantic v2 |

---

Active development.

Built by [Rushikesh](https://www.linkedin.com/in/rushikesh-yeole-9115702aa) & [Shashwat](https://www.linkedin.com/in/shashwat-awate-23127a29b).
</br>Would love to hear your thoughts or ideas! Feel free to reach out.