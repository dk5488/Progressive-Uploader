from typing import Dict, Any, Tuple, Optional
from src.state.state_manager import StateManager
from src.git.operations import GitOperations
from src.git.safety import GitSafety
from src.release.diff_builder import DiffBuilder
from src.release.release_validator import ReleaseValidator
from src.planner.replanner import Replanner
from src.notification.telegram_notifier import TelegramNotifier
import datetime
import json
from pathlib import Path

class ReleaseExecutor:
    def __init__(self, state: StateManager, git: GitOperations, safety: GitSafety, 
                 diff_builder: DiffBuilder, validator: ReleaseValidator, replanner: Replanner,
                 notifier: Optional[TelegramNotifier] = None):
        self.state = state
        self.git = git
        self.safety = safety
        self.diff_builder = diff_builder
        self.validator = validator
        self.replanner = replanner
        self.notifier = notifier or TelegramNotifier()
        self.logs_dir = state.state_dir / "logs"

    def _send_notification(self, message: str, context: str = "") -> bool:
        """Sends Telegram notification, checking return status and logging failures explicitly."""
        sent = self.notifier.send_message(message)
        if not sent:
            print(f"  Warning: Telegram notification failed to deliver for {context or 'release event'}.")
        return sent

    def _log_failure(self, release: Dict[str, Any], reason: str, stage: str):
        """Persist failure details to logs directory for post-mortem diagnosis."""
        try:
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            log_file = self.logs_dir / "failures.jsonl"
            entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "release_id": release.get("release_id"),
                "feature": release.get("feature"),
                "description": release.get("description"),
                "stage": stage,
                "reason": reason,
            }
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            print(f"  Failure logged to {log_file}")
        except Exception as e:
            print(f"  Warning: Could not write failure log: {e}")

    def _get_expected_commit_msg(self, release: Dict[str, Any], file_path: Optional[str] = None) -> str:
        feature_tag = release.get('feature', 'core').lower()
        if file_path:
            filename = Path(file_path).name
            return f"feat({feature_tag}): add {filename}"
        return f"feat({feature_tag}): {release.get('description')}"

    def _recover_state_if_needed(self, release: Dict[str, Any]) -> bool:
        """
        Checks if all files in this release are already committed.
        Returns True if it recovered and pushed, False otherwise.
        """
        files = release.get('files_involved', [])
        if not files:
            return False
            
        history = self.git.get_commit_history()
        history_str = "\n".join(history)
        
        # Check if every file involved has a corresponding commit message in history
        all_committed = True
        for f in files:
            file_name = Path(f).name
            if file_name not in history_str:
                all_committed = False
                break
                
        if all_committed:
            print("Crash recovery: All files for this release are already committed. Attempting to push...")
            success, out = self.git.push()
            if success:
                print("Crash recovery: Push successful. Updating state.")
                self._record_success(release)
                return True
            else:
                print(f"Crash recovery: Push failed. {out}")
                self._log_failure(release, f"Crash recovery push failed: {out}", "crash_recovery_push")
                return False
                
        return False

    def execute(self, release: Dict[str, Any], dry_run: bool = False) -> Tuple[bool, str]:
        rel_id = release.get('release_id', '')
        feature = release.get('feature', 'Core')
        print(f"\nExecuting Release {rel_id}: {feature} - {release.get('description')}")
        
        # 0. Crash Recovery / Idempotency Check
        if not dry_run and self._recover_state_if_needed(release):
            return True, "Recovered from previous crash or push failure."
        
        # 1. Validation
        print("Running quality gates and validation...")
        if not self.validator.validate():
            reason = "Tests/Validation failed."
            self._log_failure(release, reason, "validation")
            self._send_notification(f"⚠️ *Release {rel_id} Validation Failed*: {reason}", context=f"Release {rel_id} validation")
            return False, reason
            
        # 2. Diff and Safety Check (performed upfront for the whole release)
        diff = self.diff_builder.get_candidate_diff(release)
        is_safe, reason = self.safety.check_unrelated_changes(diff, release)
        
        if not is_safe:
            msg = f"Safety check failed: {reason}"
            self._log_failure(release, msg, "safety_check")
            self._send_notification(f"🚨 *Release {rel_id} Safety Rejection*: {reason}", context=f"Release {rel_id} safety rejection")
            return False, msg
            
        print("Safety check passed. No unrelated changes.")
        
        if dry_run:
            print("\n--- DRY RUN DIFF ---")
            print(diff)
            print("--------------------\n")
            return True, "Dry run completed."

        files = release.get('files_involved', [])
        total_files = len(files)
        
        # 3. Granular Per-File Stage, Commit, and Push
        print(f"Staging, committing, and pushing {total_files} files individually...")
        pushed_files = []
        
        for idx, file_path in enumerate(files, 1):
            file_clean = file_path.replace("\\", "/")
            self.git.add_files([file_clean])
            
            if self.git.has_staged_changes(file_clean) or self.git.has_staged_changes():
                commit_msg = self._get_expected_commit_msg(release, file_path=file_clean)
                self.git.commit(commit_msg)
                
                print(f"  [{idx}/{total_files}] Pushing {file_clean}...")
                success, out = self.git.push()
                if not success:
                    reason = f"Push failed at file {idx}/{total_files} ({file_clean}): {out}"
                    self._log_failure(release, reason, "per_file_push")
                    self._send_notification(
                        f"❌ *Release {rel_id} Failed!*\n"
                        f"*Feature:* {feature}\n"
                        f"*Failed File:* `{file_clean}` ({idx}/{total_files})\n"
                        f"*Error Output:* `{out[:200]}`",
                        context=f"Release {rel_id} push failure"
                    )
                    return False, reason
                    
                pushed_files.append(file_clean)
                print(f"  [{idx}/{total_files}] Successfully committed and pushed {file_clean}")
            else:
                print(f"  [{idx}/{total_files}] File {file_clean} already clean/committed. Skipping.")

        # 4. Check if any files were actually pushed
        if not pushed_files:
            if total_files == 0:
                reason = f"Release {rel_id} has no files assigned (already published in earlier releases)."
            else:
                reason = f"All {total_files} candidate file(s) in Release {rel_id} are already committed/published."
            
            skip_msg_cli = f"⏭️ Release {rel_id} ({feature}) SKIPPED: {reason}"
            print(f"  {skip_msg_cli}")
            
            # Record skip in state and history so the pipeline advances to next release
            self._record_skip(release, reason=reason)
            
            # Send Telegram skip notification
            skip_msg_tg = (
                f"⏭️ *Release {rel_id} Skipped*\n"
                f"*Feature:* {feature}\n"
                f"*Description:* {release.get('description')}\n"
                f"*Reason:* {reason}\n"
                f"*Status:* Marked as SKIPPED, advanced to next release."
            )
            self._send_notification(skip_msg_tg, context=f"Release {rel_id} skip")
            
            # Dynamic Replanning
            if not dry_run:
                self.replanner.replan_if_needed()
                
            return True, skip_msg_cli

        # 5. Record Success
        self._record_success(release)
        
        # 6. Build clean single summary Telegram notification
        project_state = self.state.load_state()
        completed = project_state.get('completed_releases', 0)
        total = project_state.get('total_releases', 0)
        
        files_summary = "\n".join([f"• `{f}`" for f in pushed_files[:15]])
        if len(pushed_files) > 15:
            files_summary += f"\n... and {len(pushed_files) - 15} more files"
            
        summary_msg = (
            f"🎉 *Release {rel_id} Published Successfully!*\n"
            f"*Feature:* {feature}\n"
            f"*Description:* {release.get('description')}\n"
            f"*Progress:* {completed}/{total} releases completed\n\n"
            f"*Pushed Files ({len(pushed_files)}):*\n"
            f"{files_summary}"
        )
        self._send_notification(summary_msg, context=f"Release {rel_id} success summary")
        
        # 7. Dynamic Replanning
        if not dry_run:
            self.replanner.replan_if_needed()
            
        return True, f"Release {rel_id} successfully published ({len(pushed_files)} per-file commits)."
        
    def _record_success(self, release: Dict[str, Any]):
        project_state = self.state.load_state()
        idx = release.get('_index', 0)
        
        project_state['last_successful_release_index'] = idx
        project_state['completed_releases'] = idx + 1
        project_state['last_execution'] = datetime.datetime.now().isoformat()
        
        roadmap = self.state.load_roadmap()
        if project_state['completed_releases'] >= len(roadmap.get('releases', [])):
            project_state['status'] = "COMPLETED"
            
        self.state.save_state(project_state)
        
        # Save to history
        history = self.state.load_history()
        releases_hist = history.get('releases', [])
        releases_hist.append({
            "release_id": release.get("release_id"),
            "status": "PUBLISHED",
            "timestamp": project_state['last_execution']
        })
        history['releases'] = releases_hist
        self.state.save_history(history)

    def _record_skip(self, release: Dict[str, Any], reason: str = ""):
        """Advance state index when a release is skipped because all files are already published."""
        project_state = self.state.load_state()
        idx = release.get('_index', 0)
        
        project_state['last_successful_release_index'] = idx
        project_state['completed_releases'] = idx + 1
        project_state['last_execution'] = datetime.datetime.now().isoformat()
        
        roadmap = self.state.load_roadmap()
        if project_state['completed_releases'] >= len(roadmap.get('releases', [])):
            project_state['status'] = "COMPLETED"
            
        self.state.save_state(project_state)
        
        # Save to history with SKIPPED status
        history = self.state.load_history()
        releases_hist = history.get('releases', [])
        releases_hist.append({
            "release_id": release.get("release_id"),
            "status": "SKIPPED",
            "reason": reason,
            "timestamp": project_state['last_execution']
        })
        history['releases'] = releases_hist
        self.state.save_history(history)

