import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client["users_db"]
    col = db["profiles"]
    
    new_profile = {
        "name": "Alex Chen",
        "phone": "+1 (415) 555-0199",
        "linkedin_link": "https://linkedin.com/in/alexchen-ai",
        "github_link": "https://github.com/alexchen-ai",
        "preferences": {
            "role": "AI Infrastructure & Systems Engineer",
            "location": "San Francisco / Remote"
        },
        "skills": [
            # Programming Languages
            "Python", "C++", "Rust", "Go", "SQL",
            # AI & ML Frameworks
            "PyTorch", "JAX", "TensorFlow", "Scikit-Learn", "Pandas",
            # HPC & Hardware
            "CUDA", "Triton", "GPU Architecture", "TensorRT", "NCCL", "MPI", "RDMA", "Hardware/Software Co-design",
            # Systems & Cloud Infrastructure
            "AWS", "GCP", "Linux", "Docker", "Kubernetes", "Terraform", "Virtualization", "Sandboxing",
            # Distributed Systems & Data
            "Distributed Systems", "Kafka", "PostgreSQL", "Redis", "Ray", "Spark",
            # AI Specific Systems
            "vLLM", "LLM Orchestration", "Agent Harnesses", "Model Evaluations", "RAG",
            # Performance & Observability
            "Performance Engineering", "Compiler Performance", "Profiling", "Benchmarking", "Prometheus", "Grafana", "Tracing", "Observability"
        ],
        "education": [
            {
                "degree": "Ph.D. in Computer Science",
                "branch": "Artificial Intelligence & Distributed Systems",
                "college": "Stanford University"
            },
            {
                "degree": "B.S. in Computer Science",
                "branch": "Computer Science & Mathematics",
                "college": "Massachusetts Institute of Technology (MIT)"
            }
        ],
        "projects": [
            {
                "title": "Large-Scale Distributed Training Orchestrator",
                "desc": "Designed and built a custom distributed training orchestration layer on top of AWS/GCP, Kubernetes, and PyTorch DDP. Scaled foundation model training to 4,096+ GPUs with RDMA networking, achieving 98% linear scaling efficiency."
            },
            {
                "title": "Open Source Core Contributor (vLLM & Infrastructure)",
                "desc": "Authored highly optimized custom CUDA/Triton kernels for PagedAttention. Implemented robust CI/CD pipelines, Docker containerization, and observability stacks (Prometheus/Grafana) for high-availability inference services."
            },
            {
                "title": "High-Performance Data & Agent Pipeline",
                "desc": "Developed a high-throughput backend using Go and Kafka for real-time model evaluation and agent harnesses. Migrated core data stores to PostgreSQL and optimized Pandas/SQL pipelines, reducing latency by 40%."
            }
        ]
    }
    
    result = await col.update_one(
        {"email": "demo@horizon.com"},
        {"$set": {"profile": new_profile}}
    )
    print(f"Updated demo profile. Matched {result.matched_count}, Modified {result.modified_count}.")

if __name__ == "__main__":
    asyncio.run(main())
