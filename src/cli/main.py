import click
import os
import sys
from pathlib import Path

# Configure stdout encoding on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add src to python path so imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from typing import Optional

from src.state.state_manager import StateManager
from src.git.operations import GitOperations
from src.git.safety import GitSafety
from src.llm.provider import create_llm_provider
from src.analyzer.repository_analyzer import RepositoryAnalyzer
from src.planner.roadmap_generator import RoadmapGenerator
from src.release.release_selector import ReleaseSelector
from src.release.diff_builder import DiffBuilder
from src.release.release_validator import ReleaseValidator
from src.release.release_executor import ReleaseExecutor
from src.scheduler.windows_scheduler import WindowsScheduler

from src.planner.replanner import Replanner
from src.notification.telegram_notifier import TelegramNotifier

def setup_dependencies(project_root: str, require_llm: bool = True, source_dir: Optional[str] = None):
    state = StateManager(project_root)
    git = GitOperations(project_root)
    
    # Determine the directory to analyze:
    # If source_dir is provided explicitly, use it.
    # Otherwise, if project_root is "." (or current directory) and a "source" subfolder exists,
    # analyze the "source" subfolder while keeping state in project_root.
    if source_dir:
        analyze_path = source_dir
    elif (Path(project_root) / "source").is_dir() and project_root in [".", str(Path.cwd()), ""]:
        analyze_path = str(Path(project_root) / "source")
    else:
        analyze_path = project_root

    analyzer = RepositoryAnalyzer(analyze_path)
    scheduler = WindowsScheduler(project_root)
    selector = ReleaseSelector(state)
    notifier = TelegramNotifier()

    # Only initialize LLM-dependent components when needed
    if require_llm:
        llm = create_llm_provider()
        generator = RoadmapGenerator(llm, analyzer, state)
        safety = GitSafety(git, llm)
        diff_builder = DiffBuilder(git)
        validator = ReleaseValidator(analyze_path)
        replanner = Replanner(llm, analyzer, state)
        executor = ReleaseExecutor(state, git, safety, diff_builder, validator, replanner, notifier=notifier)
    else:
        generator = None
        executor = None

    return state, git, generator, selector, executor, scheduler

@click.group()
def cli():
    """AI Incremental GitHub Publisher."""
    pass

@cli.command()
@click.option('--dir', default='.', help='Project directory')
@click.option('--source', 'source_dir', default=None, help='Source directory to analyze (defaults to source/ if present)')
def init(dir, source_dir):
    """Initializes the project and generates the roadmap."""
    click.echo("Initializing Incremental Publisher...")
    
    state, git, generator, _, _, _ = setup_dependencies(dir, source_dir=source_dir)
    
    if not git.is_git_repo():
        click.echo("Not a git repository. Initializing git...")
        git.init_repo()
        
    state.init_project()
    click.echo("State directory created.")
    
    # Generate Roadmap
    generator.generate()
    click.echo("Initialization complete. Run `publisher plan` to view roadmap.")

@cli.command()
@click.option('--dir', default='.', help='Project directory')
def plan(dir):
    """Shows the generated release roadmap with completion progress."""
    state, _, _, _, _, _ = setup_dependencies(dir, require_llm=False)
    if not state.is_initialized():
        click.echo("Project not initialized. Run `init` first.")
        return
        
    roadmap = state.load_roadmap()
    project_state = state.load_state()
    releases = roadmap.get("releases", [])
    completed_count = project_state.get("completed_releases", 0)
    last_success_idx = project_state.get("last_successful_release_index", -1)
    
    click.echo(f"Release Roadmap ({completed_count}/{len(releases)} completed):\n")
    for idx, rel in enumerate(releases):
        status_tag = "[COMPLETED]" if idx <= last_success_idx else "[PENDING]  "
        click.echo(f"{status_tag} [{idx + 1}] {rel.get('feature')}: {rel.get('description')} (Complexity: {rel.get('complexity')})")

@cli.command()
@click.option('--dir', default='.', help='Project directory')
def status(dir):
    """Shows current project status."""
    state, _, _, selector, _, _ = setup_dependencies(dir, require_llm=False)
    if not state.is_initialized():
        click.echo("Project not initialized.")
        return
        
    project_state = state.load_state()
    click.echo(f"Status: {project_state.get('status')}")
    click.echo(f"Completed Releases: {project_state.get('completed_releases', 0)} / {project_state.get('total_releases', 0)}")
    
    next_rel = selector.get_next_release()
    if next_rel:
        click.echo(f"\nNext release:")
        click.echo(f"  Feature: {next_rel.get('feature')}")
        click.echo(f"  Description: {next_rel.get('description')}")
    else:
        click.echo("\nNo pending releases.")

@cli.command()
@click.option('--dir', default='.', help='Project directory')
@click.option('--dry-run', is_flag=True, help='Simulate the release without pushing')
def release(dir, dry_run):
    """Executes the next release."""
    state, git, _, selector, executor, _ = setup_dependencies(dir)
    if not state.is_initialized():
        click.echo("Project not initialized.")
        return
        
    if selector.is_project_completed():
        click.echo("Project already completely published. No release required.")
        return
        
    next_rel = selector.get_next_release()
    if not next_rel:
        click.echo("No pending releases found.")
        return
        
    success, msg = executor.execute(next_rel, dry_run=dry_run)
    if not success:
        click.echo(f"Release failed: {msg}", err=True)
        sys.exit(1)
    else:
        click.echo(msg)

@cli.command()
@click.option('--dir', default='.', help='Project directory')
@click.option('--time', default='09:00', help='Time to schedule daily release')
def schedule(dir, time):
    """Schedules the publisher to run daily."""
    _, _, _, _, _, scheduler = setup_dependencies(dir, require_llm=False)
    scheduler.schedule_daily(time)

@cli.command()
@click.option('--dir', default='.', help='Project directory')
@click.option('--source', 'source_dir', default=None, help='Source directory to analyze')
def analyze(dir, source_dir):
    """Analyzes the repository without generating a roadmap."""
    state, git, generator, _, _, _ = setup_dependencies(dir, source_dir=source_dir)
    if not git.is_git_repo():
        click.echo("Not a git repository.")
        return
        
    state.init_project()
    click.echo("Running architecture and feature analysis...")
    file_tree = generator.analyzer.get_file_tree()
    arch = generator.llm.analyze_repository(file_tree)
    state.save_analysis("architecture.json", arch)
    
    file_contents = generator.analyzer.get_file_contents()
    features = generator.llm.identify_features(arch, file_contents, file_tree=file_tree)
    state.save_analysis("features.json", features)
    
    click.echo("Analysis complete. Saved to .incremental-publisher/analysis/")

@cli.command()
@click.option('--dir', default='.', help='Project directory')
def next(dir):
    """Shows details about the next scheduled release."""
    state, _, _, selector, _, _ = setup_dependencies(dir, require_llm=False)
    if not state.is_initialized():
        click.echo("Project not initialized.")
        return
        
    next_rel = selector.get_next_release()
    if not next_rel:
        click.echo("No pending releases.")
        return
        
    click.echo(f"Next Release ID: {next_rel.get('release_id')}")
    click.echo(f"Feature: {next_rel.get('feature')}")
    click.echo(f"Description: {next_rel.get('description')}")
    click.echo(f"Complexity: {next_rel.get('complexity')}")
    click.echo(f"Dependencies: {', '.join(next_rel.get('dependencies', []))}")
    click.echo(f"Files Involved:\n  - " + "\n  - ".join(next_rel.get('files_involved', [])))

@cli.command()
@click.option('--dir', default='.', help='Project directory')
def history(dir):
    """Shows the release history."""
    state, _, _, _, _, _ = setup_dependencies(dir, require_llm=False)
    if not state.is_initialized():
        click.echo("Project not initialized.")
        return
        
    hist = state.load_history()
    releases = hist.get("releases", [])
    if not releases:
        click.echo("No releases published yet.")
        return
        
    click.echo("Release History:\n")
    for r in releases:
        click.echo(f" - {r.get('timestamp')}: Release {r.get('release_id')}")

@cli.command()
@click.option('--dir', default='.', help='Project directory')
def doctor(dir):
    """Checks system health and requirements."""
    state, git, _, _, _, scheduler = setup_dependencies(dir, require_llm=False)
    click.echo("Running Doctor...")
    
    # Check Git
    if git.is_git_repo():
        click.echo("[OK] Git Repository Detected")
    else:
        click.echo("[WARN] Not a Git Repository")
        
    # Check API Key
    if os.environ.get("GEMINI_API_KEY"):
        click.echo("[OK] GEMINI_API_KEY is set")
    else:
        click.echo("[ERROR] GEMINI_API_KEY is missing")
        
    # Check State
    if state.is_initialized():
        click.echo("[OK] Incremental Publisher Initialized")
    else:
        click.echo("[WARN] Project Not Initialized (run `publisher init`)")

@cli.command()
@click.option('--dir', default='.', help='Project directory')
def reset_state(dir):
    """Resets publisher state safely without touching git or code."""
    state, _, _, _, _, _ = setup_dependencies(dir, require_llm=False)
    if not state.state_dir.exists():
        click.echo("No state directory found.")
        return
        
    import shutil
    try:
        shutil.rmtree(state.state_dir)
        click.echo("State safely removed. Git history and source code were not modified.")
    except Exception as e:
        click.echo(f"Failed to reset state: {e}", err=True)

if __name__ == '__main__':
    cli()
