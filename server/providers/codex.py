"""Provider Codex: invoca `codex exec` de forma não interativa.

Usa a subscrição ChatGPT autenticada no CLI. O prompt entra por stdin,
a resposta final sai por --output-last-message e, quando há schema,
--output-schema força o shape. Sandbox read-only: o servidor é o único
processo que escreve ficheiros.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .base import AIProvider, ProviderFailure, ProviderTimeout, parse_and_validate


class CodexProvider(AIProvider):
    name = "codex"

    def __init__(self, codex_bin: str = "codex", model: str | None = None, events_dir: Path | None = None):
        self.codex_bin = codex_bin
        self.model = model
        self.events_dir = events_dir

    async def complete(
        self,
        prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        system: str | None = None,
        timeout_s: int = 300,
        workdir: str | None = None,
    ) -> Any:
        full_prompt = f"{system}\n\n---\n\n{prompt}" if system else prompt
        if schema is not None:
            # Nota: --output-schema exige schemas "strict" (additionalProperties
            # false, tudo required), incompatível com o DocSpec permissivo.
            # Em vez disso o schema segue no prompt e a validação é local.
            full_prompt += (
                "\n\n---\n\nFORMATO OBRIGATÓRIO: responde APENAS com JSON válido contra este "
                f"JSON Schema, sem texto antes nem depois:\n\n```json\n{json.dumps(schema, ensure_ascii=False)}\n```"
            )
        with tempfile.TemporaryDirectory(prefix="pagecraft-codex-") as tmp:
            tmp_path = Path(tmp)
            out_file = tmp_path / "last-message.txt"
            cmd = [
                self.codex_bin,
                "exec",
                "-C",
                workdir or tmp,
                "--sandbox",
                "read-only",
                "--ephemeral",
                "--skip-git-repo-check",
                "--output-last-message",
                str(out_file),
            ]
            if self.model:
                cmd += ["-m", self.model]
            cmd.append("-")

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(full_prompt.encode("utf-8")), timeout=timeout_s
                )
            except asyncio.TimeoutError:
                self._kill(proc)
                raise ProviderTimeout(f"codex exec excedeu {timeout_s}s")

            if self.events_dir is not None:
                self.events_dir.mkdir(parents=True, exist_ok=True)
                (self.events_dir / "codex-stdout.log").write_bytes(stdout or b"")

            if proc.returncode != 0:
                raise ProviderFailure(
                    f"codex exec terminou com código {proc.returncode}",
                    detail=(stderr or b"").decode("utf-8", "replace")[-2000:],
                )
            try:
                text = out_file.read_text("utf-8")
            except FileNotFoundError:
                raise ProviderFailure(
                    "codex exec não produziu mensagem final",
                    detail=(stderr or b"").decode("utf-8", "replace")[-2000:],
                )
            if schema is None:
                return text
            return parse_and_validate(text, schema)

    @staticmethod
    def _kill(proc: asyncio.subprocess.Process) -> None:
        try:
            os.killpg(os.getpgid(proc.pid), 9)
        except (ProcessLookupError, PermissionError):
            try:
                proc.kill()
            except ProcessLookupError:
                pass
