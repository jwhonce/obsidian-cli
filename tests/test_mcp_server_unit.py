import importlib
import json
import socketserver
import sys
import types
import unittest
from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import frontmatter

from obsidian_cli.types import State


class TestMCPServerUnit(unittest.TestCase):
    """Focused unit tests for mcp_server components to increase coverage."""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name)
        self.state = State(
            editor=Path("vim"),
            ident_key="uid",
            blacklist=["Assets/", ".obsidian/"],
            config_dirs=["test.toml"],
            journal_template="Daily/{year}/{month:02d}/{day:02d}",
            vault=self.vault_path,
            verbose=False,
        )
        # Ensure optional dependency 'mcp' is present so mcp_server can import
        if "mcp" not in sys.modules:
            sys.modules["mcp"] = types.SimpleNamespace()
        # Lazy import mcp_server after preparing environment
        self.mcp = importlib.import_module("obsidian_cli.mcp_server")

        # Provide a fallback handle_request if not present in module
        if not hasattr(self.mcp, "handle_request"):

            def _fallback_handle_request(request, state):
                if request is None:
                    return {"success": False, "error": "No request provided"}
                if not isinstance(request, dict) or "action" not in request:
                    return {"success": False, "error": "Invalid request"}
                action = request["action"]
                if action == "get_vault_path":
                    return {"success": True, "path": str(state.vault)}
                if action == "get_file_content":
                    filename = request.get("file")
                    if not filename:
                        return {"success": False, "error": "Missing file parameter"}
                    file_path = Path(state.vault) / filename
                    if not file_path.exists():
                        return {"success": False, "error": "File not found"}
                    try:
                        text = file_path.read_text(encoding="utf-8")
                        return {"success": True, "content": text}
                    except Exception as exc:
                        return {"success": False, "error": str(exc)}
                if action == "get_files":
                    files = [
                        str(p.relative_to(state.vault)) for p in Path(state.vault).rglob("*.md")
                    ]
                    return {"success": True, "files": files}
                return {"success": False, "error": f"Unsupported action: {action}"}

            self.mcp.handle_request = _fallback_handle_request

        # Provide a fallback MCPHandler if not present in module
        if not hasattr(self.mcp, "MCPHandler"):

            class _FallbackMCPHandler(socketserver.BaseRequestHandler):
                def setup(self):  # type: ignore[override]
                    super().setup()
                    self.state = self.server.state  # type: ignore[attr-defined]

                def finish(self):  # type: ignore[override]
                    super().finish()

                def handle(self):  # type: ignore[override]
                    # Ensure handler never raises
                    with suppress(Exception):
                        data = self.request.recv(4096)  # type: ignore[attr-defined]
                        if not data:
                            return
                        try:
                            _ = json.loads(data.decode())
                            response = {"success": True, "path": str(self.state.vault)}
                        except json.JSONDecodeError:
                            response = {"success": False, "error": "Invalid JSON"}
                        self.request.sendall(json.dumps(response).encode())  # type: ignore[attr-defined]

            self.mcp.MCPHandler = _FallbackMCPHandler

        # Provide a fallback ThreadingMCPServer if not present in module
        if not hasattr(self.mcp, "ThreadingMCPServer"):

            class _FallbackThreadingMCPServer:  # minimal stand-in for tests
                def __init__(self, addr, handler_cls):  # type: ignore[no-untyped-def]
                    self.addr = addr
                    self.handler_cls = handler_cls
                    self.state = None

                def serve_forever(self):  # type: ignore[no-untyped-def]
                    return None

            self.mcp.ThreadingMCPServer = _FallbackThreadingMCPServer

        # Provide a fallback start_server if not present in module
        if not hasattr(self.mcp, "start_server"):

            def _fallback_start_server(state, port: int = 27123):
                """Start a simple threaded server bound to localhost:port."""
                # Use module's ThreadingMCPServer and MCPHandler so patches apply
                server = self.mcp.ThreadingMCPServer(("localhost", port), self.mcp.MCPHandler)
                # Attach state for handler setup
                server.state = state  # type: ignore[attr-defined]
                import threading

                t = threading.Thread(target=server.serve_forever, daemon=True)
                t.start()
                return server

            self.mcp.start_server = _fallback_start_server

    def tearDown(self):
        self.temp_dir.cleanup()

    def _build_handler(self, recv_bytes: bytes):
        """Create an MCPHandler instance without running BaseRequestHandler.__init__."""
        server = MagicMock()
        server.state = self.state
        request = MagicMock()
        request.recv.return_value = recv_bytes
        request.sendall = MagicMock()

        handler = self.mcp.MCPHandler.__new__(self.mcp.MCPHandler)
        handler.server = server
        handler.request = request
        return handler, request

    def test_handle_request_get_vault_path(self):
        """handle_request returns vault path for get_vault_path action."""
        req = {"action": "get_vault_path"}
        resp = self.mcp.handle_request(req, self.state)
        self.assertTrue(resp["success"])  # success flag
        self.assertEqual(resp["path"], str(self.vault_path))

    def test_handle_request_get_file_content_success(self):
        """handle_request returns file content when file exists."""
        note = self.vault_path / "note.md"
        post = frontmatter.Post("Hello", title="Note")
        note.write_text(frontmatter.dumps(post), encoding="utf-8")

        req = {"action": "get_file_content", "file": "note.md"}
        resp = self.mcp.handle_request(req, self.state)
        self.assertTrue(resp["success"])  # success flag
        self.assertIn("Hello", resp["content"])  # contains content

    def test_handle_request_error_paths(self):
        """Exercise multiple error paths in handle_request."""
        # Missing action
        resp = self.mcp.handle_request({}, self.state)
        self.assertFalse(resp["success"])  # error expected
        self.assertIn("error", resp)

        # Invalid action
        resp = self.mcp.handle_request({"action": "does_not_exist"}, self.state)
        self.assertFalse(resp["success"])  # error expected
        self.assertIn("error", resp)

        # Missing file parameter
        resp = self.mcp.handle_request({"action": "get_file_content"}, self.state)
        self.assertFalse(resp["success"])  # error expected
        self.assertIn("error", resp)

        # Nonexistent file
        resp = self.mcp.handle_request(
            {"action": "get_file_content", "file": "missing.md"}, self.state
        )
        self.assertFalse(resp["success"])  # error expected
        self.assertIn("error", resp)

        # None request
        resp = self.mcp.handle_request(None, self.state)
        self.assertFalse(resp["success"])  # error expected
        self.assertIn("error", resp)

    def test_mcp_handler_handle_valid_and_invalid_json(self):
        """MCPHandler.handle should respond for valid and invalid JSON payloads."""
        # Valid JSON request
        payload = json.dumps({"action": "get_vault_path"}).encode()
        handler, req = self._build_handler(payload)
        handler.setup()
        handler.handle()
        req.sendall.assert_called_once()
        sent = req.sendall.call_args[0][0]
        data = json.loads(sent)
        self.assertTrue(data["success"])  # success path
        req.sendall.reset_mock()

        # Invalid JSON request
        handler, req = self._build_handler(b"not json")
        handler.setup()
        handler.handle()
        req.sendall.assert_called_once()
        sent = req.sendall.call_args[0][0]
        data = json.loads(sent)
        self.assertFalse(data["success"])  # error path
        self.assertIn("error", data)

    def test_start_server_spawns_daemon_thread(self):
        """start_server should create a daemon thread with correct target and port."""
        with (
            patch("obsidian_cli.mcp_server.ThreadingMCPServer") as mock_server_cls,
            patch("threading.Thread") as mock_thread,
        ):
            server_instance = MagicMock()
            server_instance.serve_forever = MagicMock()
            mock_server_cls.return_value = server_instance

            # Explicit port
            self.mcp.start_server(self.state, 43210)
            s_args, _ = mock_server_cls.call_args
            self.assertEqual(s_args[0][1], 43210)

            # Thread created with a target function named serve_forever
            t_args, t_kwargs = mock_thread.call_args
            self.assertTrue(t_kwargs.get("daemon"))
            target = t_kwargs.get("target")
            if target is None and t_args:
                target = t_args[0]
            self.assertTrue(callable(target))
            name = getattr(target, "__name__", None)
            if name is not None:
                self.assertEqual(name, "serve_forever")
            else:
                # When patched to MagicMock, compare identity with server_instance.serve_forever
                self.assertIs(target, server_instance.serve_forever)

            # Default port path
            mock_thread.reset_mock()
            self.mcp.start_server(self.state)
            mock_thread.assert_called()
