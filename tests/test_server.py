from __future__ import annotations

import importlib.util
import unittest

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    from fastapi.testclient import TestClient

    from app.api.schemas import RunTaskResponse
    from app.api.router import get_auth_service
    from app.server import _parse_cors_allow_origins, create_app


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed in this environment")
class ServerHelperTests(unittest.TestCase):
    def test_parse_cors_allow_origins_strips_empty_entries(self) -> None:
        origins = _parse_cors_allow_origins(" https://a.example , ,https://b.example, ")
        self.assertEqual(origins, ["https://a.example", "https://b.example"])


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed in this environment")
class ServerRouteTests(unittest.TestCase):
    def test_run_task_route_returns_runner_payload(self) -> None:
        class FakeAuthService:
            def authenticate_token(self, token: str):
                if token != "valid-token":
                    raise ValueError("Invalid or expired token.")
                return type("User", (), {"username": "tester"})()

        def fake_runner(payload):
            resolved_thread_id = payload.thread_id or "generated-thread"
            return RunTaskResponse(
                task_id=resolved_thread_id,
                thread_id=resolved_thread_id,
                status="completed",
                task=payload.task,
                result="runner result",
                final_response="runner result",
                detail="mode=execute_only",
                thread_path=f"APP_DEMO/threads/{resolved_thread_id}",
            )

        app = create_app(task_runner=fake_runner)
        app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
        client = TestClient(app)

        response = client.post(
            "/api/tasks/run",
            json={"task": "ship feature", "thread_id": "thread-999", "metadata": {}},
            headers={"Authorization": "Bearer valid-token"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "task_id": "thread-999",
                "thread_id": "thread-999",
                "status": "completed",
                "task": "ship feature",
                "result": "runner result",
                "final_response": "runner result",
                "detail": "mode=execute_only",
                "thread_path": "APP_DEMO/threads/thread-999",
            },
        )


if __name__ == "__main__":
    unittest.main()
