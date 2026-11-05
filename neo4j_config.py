import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

missing = [
    name
    for name, value in (
        ("NEO4J_URI", NEO4J_URI),
        ("NEO4J_USER", NEO4J_USER),
        ("NEO4J_PASSWORD", NEO4J_PASSWORD),
    )
    if not value
]
if missing:
    raise RuntimeError(
        f"Missing Neo4j settings: {', '.join(missing)}. "
        "Set them in the project .env file."
    )