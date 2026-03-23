import argparse

from dotenv import load_dotenv

from app.service import MultiAgentService


def run_task(task: str) -> str:
    service = MultiAgentService()
    result = service.run_task(task)
    return result.final_response


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run the LangGraph multi-agent starter.")
    parser.add_argument("task", help="The task you want the agents to work on.")
    args = parser.parse_args()

    final_response = run_task(args.task)
    print(final_response)


if __name__ == "__main__":
    main()
