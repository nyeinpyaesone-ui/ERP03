# Fine-Tuning Studio

Lightweight reusable GUI/control-plane foundation for dataset preparation, fine-tuning configuration, training jobs, evaluation, and model artifact management.

## Design principles
- Lightweight core; optional integrations are adapters.
- Reusable stage definitions and immutable job records.
- Provider-neutral training configuration.
- Railway-ready deployment.
- Hugging Face integration through explicit credentials/configuration.
- PostgreSQL is used for durable metadata; object/model storage remains pluggable.

## Planned modules
1. Dashboard
2. Datasets
3. Training Stages
4. Jobs
5. Evaluations
6. Models/Adapters
7. Integrations
8. Settings

## Configuration
Runtime configuration belongs in environment variables. Never commit credentials, tokens, or passwords.

See the source materials supplied with the project for the ERP03 implementation conventions and PostgreSQL data-model references.
