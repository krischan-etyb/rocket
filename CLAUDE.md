# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**Rocket** is a Visual Studio project workspace currently in early development stage.

## Development Environment

- **IDE**: Visual Studio (Windows)
- **Platform**: Windows (.NET)
- **Version Control**: Git (repository not yet initialized)

## Project Structure

```
rocket/
├── .vs/              # Visual Studio configuration (git-ignored)
└── CLAUDE.md         # This file
```

## Build & Run

Commands will be added as the project develops:

```bash
# Build
# dotnet build

# Run
# dotnet run

# Clean
# dotnet clean
```

## Testing

Testing commands will be added once tests are implemented:

```bash
# Run all tests
# dotnet test

# Run specific test
# dotnet test --filter "TestName"
```

## Code Standards

- Follow standard C# naming conventions
- Use meaningful variable and method names
- Add XML documentation comments for public APIs
- Keep methods focused and single-purpose

## Git Configuration

The `.vs` directory contains Visual Studio-specific configuration and is excluded from version control via `.gitignore`.

## Notes for Claude Code

- Always read files before modifying them
- Prefer editing existing files over creating new ones
- Follow established patterns in the codebase
- Ask for clarification when requirements are ambiguous

---

*Last updated: 2026-01-28*
