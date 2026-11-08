---
tags: [skill-creator]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

In the frontend, add a BatteryCard component that shows the live battery state of charge and power for a device. The backend endpoint is GET /api/devices/<id>/battery/ returning {"soc": number, "power_w": number, "updated_at": string}. It should refresh every 10 seconds.
