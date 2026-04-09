import os
import logging
from typing import List, Dict, Any

from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase

load_dotenv()
log = logging.getLogger("graph")

_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD", "password")),
        )
    return _driver


async def setup():
    """Run on startup — creates uniqueness constraints."""
    async with _get_driver().session() as s:
        await s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE")
        await s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE")
        await s.run("CREATE INDEX transitions_count IF NOT EXISTS FOR ()-[t:TRANSITIONS_TO]-() ON (t.count)")
    log.info("Graph constraints ready.")


async def evolve(role: str, skills: List[str]):
    """Strengthen graph from a fresh JD signal. Only called on cache misses."""
    if not skills:
        return

    async def _tx(tx):
        await tx.run(
            """
            MERGE (r:Role {name: toLower($role)})
            WITH r
            UNWIND $skills AS raw
            MERGE (s:Skill {name: toLower(raw)})
            MERGE (r)-[e:REQUIRES]->(s)
              ON CREATE SET e.weight = 1.0, e.count = 1
              ON MATCH  SET e.count = e.count + 1,
                            e.weight = e.weight + 0.1
            """,
            role=role, skills=skills,
        )

    try:
        async with _get_driver().session() as s:
            await s.execute_write(_tx)
        log.info(f"Graph evolved: '{role}' +{len(skills)} skills")
    except Exception as e:
        log.error(f"Graph evolve failed for '{role}': {e}")


async def evolve_paths(paths: List[List[str]]):
    """
    Ingest real career progressions extracted from synthesis evidence.
    Creates Role nodes and weighted TRANSITIONS_TO edges for each consecutive pair.
    """
    if not paths:
        return

    async def _tx(tx):
        await tx.run(
            """
            UNWIND $paths AS path
            UNWIND range(0, size(path) - 2) AS i
            MERGE (r1:Role {name: toLower(path[i])})
            MERGE (r2:Role {name: toLower(path[i + 1])})
            MERGE (r1)-[t:TRANSITIONS_TO]->(r2)
              ON CREATE SET t.count = 1
              ON MATCH  SET t.count = t.count + 1
            """,
            paths=paths,
        )

    try:
        async with _get_driver().session() as s:
            await s.execute_write(_tx)
        log.info(f"Paths evolved: {len(paths)} career tracks ingested.")
    except Exception as e:
        log.error(f"evolve_paths failed: {e}")


async def find_trajectories(skills: List[str], limit: int = 3) -> List[Dict[str, Any]]:
    """
    Find top roles by weighted skill overlap, then walk TRANSITIONS_TO forward
    to the farthest reachable node. Returns full trajectory per matched role.
    Used as prior context in synthesis — shows the graph's known best paths.
    """
    async with _get_driver().session() as s:
        top_res = await s.run(
            """
            UNWIND $skills AS raw
            MATCH (s:Skill {name: toLower(raw)})<-[e:REQUIRES]-(r:Role)
            WITH r, sum(e.weight) AS score, collect(s.name) AS matched
            ORDER BY score DESC
            LIMIT $limit
            RETURN r.name AS role, score, matched
            """,
            skills=skills, limit=limit,
        )
        top_roles = await top_res.data()

        if not top_roles:
            return []

        results = []
        for record in top_roles:
            start = record["role"]
            traj_res = await s.run(
                """
                MATCH path = (r:Role {name: $role})-[:TRANSITIONS_TO*0..15]->(terminal:Role)
                RETURN [n IN nodes(path) | n.name] AS trajectory
                ORDER BY length(path) DESC
                LIMIT 1
                """,
                role=start,
            )
            traj_data = await traj_res.data()
            trajectory = traj_data[0]["trajectory"] if traj_data else [start]

            results.append({
                "role": start,
                "score": record["score"],
                "matched": record["matched"],
                "trajectory": trajectory,
                "terminal": trajectory[-1],
            })

        return results


# async def find_roles(skills: List[str], limit: int = 3) -> List[Dict[str, Any]]:
#     """Skill-overlap role match without trajectory — used as fallback check."""
#     async with _get_driver().session() as s:
#         res = await s.run(
#             """
#             UNWIND $skills AS raw
#             MATCH (s:Skill {name: toLower(raw)})<-[e:REQUIRES]-(r:Role)
#             WITH r, sum(e.weight) AS score, collect(s.name) AS matched
#             ORDER BY score DESC
#             LIMIT $limit
#             RETURN r.name AS role, score, matched
#             """,
#             skills=skills, limit=limit,
#         )
#         return await res.data()