Automation Controller for Max (AI Operator)

Overview
- This controller orchestrates subagents to handle non-sensitive automation tasks across growth, content, reporting, and internal operations. Any highly sensitive actions (e.g., API keys provisioning, creating email accounts) require explicit human approvals via a defined gate.
- The goal is to maximize autonomy for repetitive, low-risk work while preserving safety for credentialed or identity-bound actions.

Core components
- Task Catalog: A catalog of tasks that can be executed automatically. Each task has an id, name, description, and whether it can run autonomously.
- Policy File: Defines allowed actions, allowed agents, and required approvals for sensitive operations.
- Approval Gate: A human-in-the-loop mechanism to review and approve high-risk actions before execution.
- Secrets Vault: A secure store (or reference to one) for API keys and credentials. Access controlled and rotated.
- Automation Controller (Master): The orchestrator that spawns subagents, routes tasks, and logs outcomes.
- Subagents: Individual agents responsible for executing tasks (growth, content, ops, etc.). Distinguish between run (one-off) vs. session (persistent) modes where supported.

Operating model
- Non-sensitive tasks: Can run autonomously under the Automation Controller.
- Sensitive tasks: Require approval gate and will not execute until approved.
- Logging: All actions produce a trace in a central log to support auditing.
- Security: Limit capabilities of subagents; avoid exposing credentials or external write access unless approved.

How to use
1) Define your task catalog and policy file (below) in JSON/YAML formats.
2) Add an Approval Gate workflow: when a subagent requests a sensitive action, generate a human-readable approval prompt with action scope, risk, and required approvals.
3) Use the Secrets Vault for credentials, with access controls and rotation.
4) Spawn subagents as needed via sessions_spawn (mode/run) with appropriate context (thread support depending on channel).
5) Monitor and adjust the policy as you learn what tasks are acceptable to automate.

Next steps
- Fill in the Task Catalog (TASK_CATALOG.json) and Policy (POLICY.md) with your governance preferences.
- Create a Secrets Vault template (SECRETS_VAULT.example.json) and document how to populate it securely.
- If you want, I can generate concrete templates for the policy file and approval prompts.
