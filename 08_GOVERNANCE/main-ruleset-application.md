# EPM main ruleset application

This file is the human-boundary procedure for issue #10.

The intended repository ruleset is committed as:

[`08_GOVERNANCE/main-ruleset-target.json`](main-ruleset-target.json)

## Target

Protect the default branch (`main`) without retargeting or rewriting the frozen v0.1.1 runtime release:

`87903f2d53531bf28d97f1271af62b6d9b3e64be`

The ruleset must not change the `v0.1.1` tag or `release/epm-v0.1.1-2026-09-14` branch.

## Required checks

The certified workflow job names are:

- `test (3.12)`
- `test (3.13)`

The ruleset requires both and enables strict/up-to-date status checking.

## Required protections

The JSON target requires:

- pull request path before `main` can change;
- both EPM Runtime CI matrix jobs green;
- branch current with `main` before merge;
- branch deletion blocked;
- force pushes blocked;
- review conversations resolved;
- no mandatory second reviewer, preserving a workable solo-maintainer path;
- emergency bypass limited to GitHub user id `304829193` and only through a pull request.

The bypass mode is deliberately `pull_request`, not `always`. The designated maintainer can invoke an emergency PR bypass when necessary, but the ruleset does not create a routine direct-push escape hatch.

## Apply in GitHub

Repository administrators can import the JSON through:

**Settings → Rules → Rulesets → New ruleset → Import a ruleset**

Import `main-ruleset-target.json`, inspect the resulting settings, and activate the ruleset.

After activation, verify:

1. GitHub reports one active branch ruleset targeting the default branch.
2. A direct update to `main` is rejected outside the PR path.
3. A PR cannot merge while either `test (3.12)` or `test (3.13)` is missing or failing.
4. A PR must be up to date with `main` before merge.
5. Force-push and deletion are blocked.
6. The v0.1.1 tag still resolves exactly to `87903f2d53531bf28d97f1271af62b6d9b3e64be`.

## Why this file exists

The connected GitHub integration can inspect rulesets but does not have repository-administration write authority. The desired control is therefore represented as auditable governance-as-code rather than simulated.
