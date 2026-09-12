from pathlib import Path

from loguru import logger

from .base_node import BaseNode
from ..state import GraphState
from ..tools import git_create_patch, read_script


class SavePatchNode(BaseNode):
    def invoke(self, state: GraphState):
        worktree_root = state["worktree_root"]
        repo_root = Path(state["repo_root"])
        op = state["op"]

        package_dir = repo_root / state["artifact_dir"] / "patches" / op

        patch_path = package_dir / "changes.patch"
        apply_script_path = package_dir / "apply.sh"

        try:
            package_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            git_create_patch(
                repo_root=worktree_root,
                patch_path=str(patch_path),
            )

            self._create_apply_script(
                apply_script_path,
            )

            return {
                "patch_package": str(package_dir),
                "patch_path": str(patch_path),
                "patch_apply_script": str(apply_script_path),
                "patch_succeeded": True,
                "patch_error": "",
            }

        except Exception as exc:
            return {
                "patch_package": "",
                "patch_path": "",
                "patch_apply_script": "",
                "patch_succeeded": False,
                "patch_error": str(exc),
            }

    @staticmethod
    def _create_apply_script(
        script_path: Path,
    ):
        script = read_script("apply_patch.sh")
        script_path.write_text(script, encoding="utf-8")
        script_path.chmod(0o755)

    def print_result(self, result: GraphState):
        if result.get("patch_succeeded", False):
            logger.success(
                "Patch package saved: {}",
                result["patch_package"],
            )
            logger.info(
                "Apply with: {}",
                result["patch_apply_script"],
            )
        else:
            logger.error(
                "Failed to create patch package: {}",
                result.get("patch_error", ""),
            )
