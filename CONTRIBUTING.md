# Contributing to InterviewPilot AI

Thank you for your interest in contributing! 🎉 This guide will help you get set up and understand how we work.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Branching Strategy](#branching-strategy)
- [Commit Convention](#commit-convention)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)

---

## Code of Conduct

Please be respectful and constructive in all interactions. We follow the [Contributor Covenant](https://www.contributor-covenant.org/) code of conduct.

---

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/Azziz14/Rag_Placement_Copilot-/issues) first.
2. Open a new issue using the **Bug Report** template.
3. Include: steps to reproduce, expected behaviour, actual behaviour, environment details.

### Suggesting Features

1. Open a new issue using the **Feature Request** template.
2. Describe the problem it solves and your proposed solution.

### Submitting Code

For anything beyond a trivial typo fix, **open an issue first** so we can discuss the approach before you invest time writing code.

---

## Development Setup

See the full [Getting Started](README.md#getting-started) guide in the README.

**Quick summary:**

```bash
# Backend
python -m venv .venv && .venv/Scripts/activate  # Windows
pip install -r backend/requirements.txt
python -m spacy download en_core_web_sm
cp backend/.env.example backend/.env  # then fill in your keys

# Frontend
cd frontend && npm install
```

---

## Branching Strategy

| Branch | Purpose |
|---|---|
| `main` | Production-ready code. Protected. |
| `develop` | Integration branch for features |
| `feature/<name>` | New features |
| `fix/<name>` | Bug fixes |
| `docs/<name>` | Documentation only |
| `chore/<name>` | Tooling, deps, refactors |

Always branch off `develop`, not `main`.

```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-feature
```

---

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

**Types:**

| Type | Use for |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation changes only |
| `style` | Formatting, missing semicolons, etc. |
| `refactor` | Code change that is neither a fix nor a feature |
| `test` | Adding or updating tests |
| `chore` | Dependency updates, tooling changes |

**Examples:**

```bash
git commit -m "feat(interview): add adaptive difficulty scoring"
git commit -m "fix(auth): handle expired JWT tokens gracefully"
git commit -m "docs(readme): update environment variable table"
```

---

## Pull Request Process

1. Ensure your branch is up to date with `develop`.
2. Run linting before pushing:
   ```bash
   # Backend
   cd backend && python -m flake8 app/

   # Frontend
   cd frontend && npm run lint
   ```
3. Fill in the **Pull Request template** completely.
4. Request review from at least one maintainer.
5. PRs are squash-merged into `develop`.

---

## Coding Standards

### Python (Backend)

- Follow **PEP 8** style guide.
- All functions and classes must have **docstrings**.
- Use **type hints** on all function signatures.
- Keep service functions focused — one responsibility per function.
- Never commit secrets or API keys.

### JavaScript/TypeScript (Frontend)

- Use **functional React components** with hooks.
- Keep components small and focused.
- Extract reusable logic into custom hooks.
- Use descriptive variable names — no `x`, `tmp`, `data`.

### General

- Write self-documenting code; add comments only for non-obvious logic.
- Keep PRs focused — one feature or fix per PR.
- Delete your branch after it is merged.
