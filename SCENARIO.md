# SCENARIO.md - Engagement Brief

## Client: Initech Cloud

Initech Cloud is a (fictional) mid-size e-commerce company that migrated its
infrastructure to the cloud eighteen months ago. Growth has been fast, the platform
team is small, and a recent internal audit raised concerns that access controls
across their tenant - user roles, service accounts, storage, and secrets management
- may not have kept pace with the buildout. Initech's leadership has engaged you to
perform an internal penetration test of their cloud environment before their next
compliance review.

## Engagement brief

You've been provided a single set of credentials matching what a real attacker
might realistically obtain first: a low-privilege internal account, reportedly
reused from a default onboarding password that was never rotated. Your engagement
is scoped to this cloud tenant only. Starting from this single foothold, your goal
is to determine how far an attacker could actually get - identify
misconfigurations, chase any credentials or access you uncover along the way, and
determine whether a low-privilege intern account could realistically be leveraged
into full administrative control of the tenant. Document every finding as you go;
your final report should let Initech's engineering team reproduce and fix each
issue.

## Rules of engagement

- In scope: the Initech Cloud console and API running in this lab environment only.
- Starting access: the credential documented in [README.md](README.md) (`j.intern` /
  `Welcome2024!`). No other credentials are provided - anything else must be
  discovered during the assessment.
- Goal: escalate from this single low-privilege foothold to the broadest access you
  can achieve, and be able to explain exactly how (which misconfiguration, which
  request, which response) at each step.
- Out of scope: this is a closed lab exercise - there is no real external network to
  test, and no real Initech Cloud exists. Do not attempt techniques against real
  Azure/AWS tenants using anything learned here without separate, explicit
  authorization for those environments.

Good luck. Check [VULNERABILITIES.md](VULNERABILITIES.md) only after you've made a
real attempt on your own - it's the answer key.
