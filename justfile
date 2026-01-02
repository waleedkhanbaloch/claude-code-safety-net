# Install dependencies
setup:
    uv sync
    uv run pre-commit install

# Run linter, type checker, dead code detection, and tests
check:
    # Run linter
    uv run ruff check --fix
    # Run type checker
    uv run mypy .
    # Run dead code detection
    uv run vulture
    # Run tests with coverage report
    uv run pytest --cov=scripts --cov-report=json --cov-report=term-missing

# Bump version and generate changelog
bump:
    @test "$(git branch --show-current)" = "main" || (echo "Error: Must be on main branch to release" && exit 1)
    uv run cz bump --no-verify
    uv sync
    git add uv.lock
    git commit --amend --no-edit --no-verify
    @# Move tag to amended commit (cz bump tagged the pre-amend commit)
    git tag -f $(git describe --tags --abbrev=0)
    git push -u origin HEAD --follow-tags
    gh release create $(git describe --tags --abbrev=0) --notes "$(uv run cz changelog $(git describe --tags --abbrev=0) --dry-run)"
