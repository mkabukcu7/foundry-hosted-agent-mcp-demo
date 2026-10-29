"""One role per Foundry container; no nested local specialist processes."""

import asyncio
import os


async def main():
    role = os.environ.get("CONTRACT_ASSURANCE_ROLE")
    if role == "orchestrator":
        from agent.contract_assurance import main as run
    elif role in {"contract", "rfp"}:
        from agent.contract_specialist import main as run
    else:
        raise ValueError("Set CONTRACT_ASSURANCE_ROLE to orchestrator, contract, or rfp.")
    await run()


if __name__ == "__main__":
    asyncio.run(main())