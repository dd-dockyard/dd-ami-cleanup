import os

from rich.console import Console

# Not using .github.running_in_github_actions here because that file
# imports this one.

# For regular console output we wrap at 100
console = Console(
    force_terminal=True if "GITHUB_ACTIONS" in os.environ else None,
    width=100 if "GITHUB_ACTIONS" in os.environ else None,
)

# For logs we basically don't want to wrap at all in CI
# (if we try and force it to be unwrapped on a regular console
# it breaks, sadly)
log_console = Console(
    force_terminal=True if "GITHUB_ACTIONS" in os.environ else None,
    width=4096 if "GITHUB_ACTIONS" in os.environ else None,
)
