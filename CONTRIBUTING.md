# Contributing to ERP03

First off, thank you for considering contributing to ERP03! It's people like you that make ERP03 such a great tool.

Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title** for the issue to identify the problem.
* **Describe the exact steps which reproduce the problem** in as many details as possible.
* **Provide specific examples to demonstrate the steps**.
* **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
* **Explain which behavior you expected to see instead and why.**
* **Include environment details**: ERPNext version, Docker version, OS, etc.

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title** for the issue to identify the suggestion.
* **Provide a detailed description of the suggested enhancement** with specific examples.
* **Explain why this enhancement would be useful** to most ERP03 users.
* **List some other applications where this enhancement exists** (if applicable).

### Pull Requests

* Fill in the required template provided in the PR description.
* Follow the coding conventions used in the project.
* Include comments in your code explaining your rationale.
* Update documentation as necessary.
* Ensure all tests pass (if applicable).

## Development Setup

### Prerequisites

* Git
* Docker & Docker Compose
* VS Code (recommended) with DevContainers extension

### Setting Up Your Development Environment

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ERP03.git
   cd ERP03
   ```
3. Open in VS Code and reopen in container (Ctrl+Shift+P → "Reopen in Container").
4. The DevContainer will automatically install all necessary dependencies.

### Making Changes

1. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes and commit them using conventional commits:
   ```bash
   git commit -m "feat: add new OIDC provider support"
   ```
3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
4. Open a Pull Request on GitHub.

## Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

* `feat`: A new feature
* `fix`: A bug fix
* `docs`: Documentation only changes
* `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc.)
* `refactor`: A code change that neither fixes a bug nor adds a feature
* `perf`: A code change that improves performance
* `test`: Adding missing tests or correcting existing tests
* `chore`: Changes to the build process or auxiliary tools and libraries

### Examples

```
feat(oidc): add Auth0 provider support
fix(docker): resolve health check timeout issue
docs(readme): update deployment instructions
refactor(config): simplify environment variable handling
```

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a build.
2. Update the README.md or other documentation with details of changes to the interface, including new environment variables, exposed ports, useful file locations, and container parameters.
3. Increase the version numbers in any examples files and the README.md to reflect the new version that the pull request represents.
4. You may merge the Pull Request in once you have the sign-off of at least one other developer, or if you do not have permission to do that, you may request the second reviewer to merge it for you.

## Code Review Process

Our team reviews pull requests on a regular basis. We will respond within 3-5 business days. During the review, we may request changes. Please respond to feedback in a timely manner.

## Questions?

Feel free to open an issue with the "question" label if you have any questions about contributing!

Thank you for your contributions! 🎉
