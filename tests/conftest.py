import pytest


@pytest.fixture
def sample_request() -> dict[str, str]:
    return {
        "repository": "octo/demo",
        "task": "Add JWT authentication to the API",
    }
