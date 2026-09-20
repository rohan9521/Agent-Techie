import json
from collections.abc import Mapping
from typing import Any, Protocol, cast
from urllib.request import Request, urlopen


class GitHubService(Protocol):
    def get_repository(self, repository: str) -> dict[str, object]: ...

    def get_file(
        self, repository: str, path: str, ref: str = "main"
    ) -> dict[str, object]: ...

    def create_branch(
        self, repository: str, branch: str, base: str = "main"
    ) -> dict[str, object]: ...

    def create_commit(
        self,
        repository: str,
        branch: str,
        message: str,
        files: Mapping[str, str],
    ) -> dict[str, object]: ...

    def create_pull_request(
        self,
        repository: str,
        title: str,
        head: str,
        base: str = "main",
        body: str = "",
    ) -> dict[str, object]: ...

    def get_pull_request(self, repository: str, number: int) -> dict[str, object]: ...


class InMemoryGitHubService:
    """Safe no-op GitHub implementation for tests and offline development."""

    def __init__(self) -> None:
        self.branches: list[dict[str, object]] = []
        self.pull_requests: list[dict[str, object]] = []

    def get_repository(self, repository: str) -> dict[str, object]:
        return {"full_name": repository, "offline": True}

    def get_file(
        self, repository: str, path: str, ref: str = "main"
    ) -> dict[str, object]:
        return {"repository": repository, "path": path, "ref": ref, "content": ""}

    def create_branch(
        self, repository: str, branch: str, base: str = "main"
    ) -> dict[str, object]:
        value: dict[str, object] = {
            "repository": repository,
            "branch": branch,
            "base": base,
        }
        self.branches.append(value)
        return value

    def create_commit(
        self,
        repository: str,
        branch: str,
        message: str,
        files: Mapping[str, str],
    ) -> dict[str, object]:
        return {
            "repository": repository,
            "branch": branch,
            "message": message,
            "files": dict(files),
            "offline": True,
        }

    def create_pull_request(
        self,
        repository: str,
        title: str,
        head: str,
        base: str = "main",
        body: str = "",
    ) -> dict[str, object]:
        value: dict[str, object] = {
            "number": len(self.pull_requests) + 1,
            "repository": repository,
            "title": title,
            "head": head,
            "base": base,
            "body": body,
            "offline": True,
        }
        self.pull_requests.append(value)
        return value

    def get_pull_request(self, repository: str, number: int) -> dict[str, object]:
        for pull_request in self.pull_requests:
            if (
                pull_request.get("repository") == repository
                and pull_request.get("number") == number
            ):
                return dict(pull_request)
        raise KeyError(f"pull request {repository}#{number} not found")


class HttpGitHubService:
    """Small optional HTTP adapter using only the Python standard library."""

    def __init__(self, token: str, api_url: str = "https://api.github.com") -> None:
        if not token:
            raise ValueError("GitHub token is required")
        self.token = token.rstrip()
        self.api_url = api_url.rstrip("/")

    def _request(
        self,
        path: str,
        method: str = "GET",
        payload: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(
            f"{self.api_url}{path}",
            data=body,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer " + self.token,
                "Content-Type": "application/json",
            },
        )
        with urlopen(request, timeout=20) as response:
            value: Any = json.loads(response.read())
        return cast(dict[str, object], value)

    def get_repository(self, repository: str) -> dict[str, object]:
        return self._request(f"/repos/{repository}")

    def get_file(
        self, repository: str, path: str, ref: str = "main"
    ) -> dict[str, object]:
        return self._request(f"/repos/{repository}/contents/{path}?ref={ref}")

    def create_branch(
        self, repository: str, branch: str, base: str = "main"
    ) -> dict[str, object]:
        ref = self._request(f"/repos/{repository}/git/ref/heads/{base}")
        sha = str(cast(dict[str, Any], ref["object"])["sha"])
        return self._request(
            f"/repos/{repository}/git/refs",
            "POST",
            {"ref": f"refs/heads/{branch}", "sha": sha},
        )

    def create_commit(
        self,
        repository: str,
        branch: str,
        message: str,
        files: Mapping[str, str],
    ) -> dict[str, object]:
        current = self._request(f"/repos/{repository}/git/ref/heads/{branch}")
        current_sha = str(cast(dict[str, Any], current["object"])["sha"])
        tree = self._request(
            f"/repos/{repository}/git/trees",
            "POST",
            {
                "base_tree": current_sha,
                "tree": [
                    {"path": path, "mode": "100644", "type": "blob", "content": content}
                    for path, content in files.items()
                ],
            },
        )
        commit = self._request(
            f"/repos/{repository}/git/commits",
            "POST",
            {"message": message, "tree": tree["sha"], "parents": [current_sha]},
        )
        return self._request(
            f"/repos/{repository}/git/refs/heads/{branch}",
            "PATCH",
            {"sha": commit["sha"]},
        )

    def create_pull_request(
        self,
        repository: str,
        title: str,
        head: str,
        base: str = "main",
        body: str = "",
    ) -> dict[str, object]:
        return self._request(
            f"/repos/{repository}/pulls",
            "POST",
            {"title": title, "head": head, "base": base, "body": body},
        )

    def get_pull_request(self, repository: str, number: int) -> dict[str, object]:
        return self._request(f"/repos/{repository}/pulls/{number}")
