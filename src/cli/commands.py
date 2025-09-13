"""CLI commands for Edgar-AI."""

import argparse
import asyncio
from pathlib import Path
from typing import List

from extraction.orchestrator import ExtractionPipeline
from interfaces.models import Document
from storage.memory import MemoryStore
from edgar.config import settings
import os
import json

try:
    # Optional import; only needed for the `send` command
    from openai import AsyncOpenAI  # type: ignore
except Exception:  # pragma: no cover
    AsyncOpenAI = None  # Will be validated at runtime


async def extract_command(args):
    """Extract data from documents."""
    pipeline = ExtractionPipeline()
    
    # Load documents
    documents = []
    for path in args.documents:
        doc_path = Path(path)
        if doc_path.is_file():
            content = doc_path.read_text()
            doc = Document(
                id=doc_path.stem,
                text=content,
                metadata={"source": "file", "path": str(doc_path)}
            )
            documents.append(doc)
        elif doc_path.is_dir():
            for file_path in doc_path.glob("*.txt"):
                content = file_path.read_text()
                doc = Document(
                    id=file_path.stem,
                    text=content,
                    metadata={"source": "file", "path": str(file_path)}
                )
                documents.append(doc)
    
    print(f"Processing {len(documents)} documents...")
    
    # Process documents
    if args.batch:
        results = await pipeline.process_batch(
            documents, 
            max_concurrent=args.concurrent
        )
    else:
        results = []
        for doc in documents:
            print(f"Processing {doc.id}...")
            result = await pipeline.process(doc)
            results.append(result)
    
    # Output results
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        import json
        with open(output_path, "w") as f:
            json.dump(
                [r.model_dump() for r in results],
                f,
                indent=2,
                default=str
            )
        print(f"Results saved to {output_path}")
    else:
        # Print summary
        for result in results:
            print(f"\nDocument: {result.document_id}")
            print(f"Goal: {result.goal.overview}")
            print(f"Rows extracted: {len(result.rows)}")
            print(f"Quality score: {result.decision.quality_score:.2f}")


async def schema_command(args):
    """Manage schemas."""
    memory = MemoryStore()
    
    if args.action == "list":
        schemas = await memory.list_schemas()
        print(f"Found {len(schemas)} schemas:\n")
        
        for schema in schemas:
            print(f"ID: {schema.id}")
            print(f"Goal: {schema.goal_id}")
            print(f"Name: {schema.name}")
            print(f"Fields: {len(schema.fields)}")
            print()
    
    elif args.action == "show":
        schema = await memory.find_schema(args.goal_id)
        if schema:
            print(f"Schema: {schema.name}")
            print(f"Description: {schema.description}")
            print("\nFields:")
            for field in schema.fields:
                req = "required" if field.required else "optional"
                print(f"  - {field.name} ({field.type}, {req}): {field.description}")
        else:
            print(f"No schema found for goal: {args.goal_id}")


async def server_command(args):
    """Run the gateway server."""
    import uvicorn
    from gateway.app.main import app
    
    print(f"Starting Edgar-AI Gateway on {args.host}:{args.port}")
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload
    )


async def send_command(args):
    """Send a prompt and a credit agreement to the OpenAI API and print the response."""
    if AsyncOpenAI is None:
        raise RuntimeError("openai package is not available. Please ensure it is installed in this environment.")

    # Resolve the OpenAI API key with safe fallbacks (do not print it)
    api_key = (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("EDGAR_AI_OPENAI_API_KEY")
        or os.getenv("EDGAR_OPENAI_API_KEY")
        or settings.openai_api_key
    )
    if not api_key:
        # As a final fallback, try to read from a local .env file without importing extra deps
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key in {"OPENAI_API_KEY", "EDGAR_AI_OPENAI_API_KEY", "EDGAR_OPENAI_API_KEY"} and val:
                    api_key = val
                    break
    if not api_key:
        raise RuntimeError(
            "No OpenAI API key found. Set OPENAI_API_KEY or EDGAR_AI_OPENAI_API_KEY in your environment/.env."
        )

    # Resolve prompt and agreement paths
    prompt_path = Path(args.prompt) if args.prompt else Path("ENHANCED_universal_debt_extraction_prompt.md")
    agreement_path = Path(args.agreement) if args.agreement else Path("scratch/debt_extraction_testing/rf_monolithics_loan.txt")

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    if not agreement_path.exists():
        raise FileNotFoundError(f"Agreement file not found: {agreement_path}")

    prompt_text = prompt_path.read_text()
    agreement_text = agreement_path.read_text()

    # Build chat messages
    messages = [
        {"role": "system", "content": prompt_text},
        {
            "role": "user",
            "content": (
                "You will receive the full text of a credit agreement. "
                "Follow the system instructions to extract the required information.\n\n"
                f"CREDIT AGREEMENT TEXT:\n\n{agreement_text}"
            ),
        },
    ]

    # Prepare request
    model = args.model or settings.extractor_model
    temperature = 0.0 if args.temperature is None else float(args.temperature)

    client = AsyncOpenAI(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=messages,
        )
    finally:
        # ensure the HTTP client inside OpenAI SDK is closed
        try:
            await client.close()
        except Exception:
            pass

    # Print the first choice content (plain text)
    choice = response.choices[0]
    content = choice.message.content if hasattr(choice, "message") else None
    if not content:
        print(json.dumps(response.model_dump(), indent=2, default=str))
    else:
        print(content)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Edgar-AI: Automated SEC document extraction"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Extract command
    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract data from documents"
    )
    extract_parser.add_argument(
        "documents",
        nargs="+",
        help="Document files or directories"
    )
    extract_parser.add_argument(
        "-o", "--output",
        help="Output file path"
    )
    extract_parser.add_argument(
        "-b", "--batch",
        action="store_true",
        help="Process documents in batch"
    )
    extract_parser.add_argument(
        "-c", "--concurrent",
        type=int,
        default=5,
        help="Max concurrent extractions"
    )
    
    # Schema command
    schema_parser = subparsers.add_parser(
        "schema",
        help="Manage extraction schemas"
    )
    schema_parser.add_argument(
        "action",
        choices=["list", "show"],
        help="Schema action"
    )
    schema_parser.add_argument(
        "goal_id",
        nargs="?",
        help="Goal ID for show action"
    )
    
    # Server command
    server_parser = subparsers.add_parser(
        "server",
        help="Run the gateway server"
    )
    server_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to"
    )
    server_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to"
    )
    server_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload"
    )

    # Send command
    send_parser = subparsers.add_parser(
        "send",
        help=(
            "Send a prompt and a credit agreement to the OpenAI API using your environment API key. "
            "Defaults are chosen from this repo if not provided."
        ),
    )
    send_parser.add_argument(
        "--prompt",
        help="Path to the prompt file (default: ENHANCED_universal_debt_extraction_prompt.md)",
    )
    send_parser.add_argument(
        "--agreement",
        help="Path to a credit agreement text file (default: scratch/debt_extraction_testing/rf_monolithics_loan.txt)",
    )
    send_parser.add_argument(
        "--model",
        help="Model name (default from settings. extractor model)",
    )
    send_parser.add_argument(
        "--temperature",
        type=float,
        help="Sampling temperature (default: 0.0)",
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Route to appropriate command
    if args.command == "extract":
        await extract_command(args)
    elif args.command == "schema":
        await schema_command(args)
    elif args.command == "server":
        await server_command(args)
    elif args.command == "send":
        await send_command(args)


if __name__ == "__main__":
    asyncio.run(main())
