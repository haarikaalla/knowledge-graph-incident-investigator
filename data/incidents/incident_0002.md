---
id: incident_0002
synthetic: true
date: 2026-05-02
technique_ids: [T1021.002, T1053.005]
severity: critical
---

# Incident 0002: Lateral movement via admin shares and scheduled tasks

Endpoint detection flagged an unusual process spawning svchost.exe with
command-line arguments referencing an administrative share on a finance
subnet host (T1021.002 - SMB/Windows Admin Shares). Investigation found the
source host had been compromised three days earlier via a vulnerable VPN
appliance. The actor copied a renamed binary to \\FIN-SRV02\C$\Windows\Temp
and created a scheduled task (T1053.005 - Scheduled Task) set to execute at
2:00 AM local time, outside normal admin working hours. The task launched a
credential-dumping tool against LSASS memory before the SOC isolated the
host. Three additional hosts on the same subnet showed the identical
scheduled-task naming pattern, suggesting automated propagation rather than
manual lateral movement.

Lessons: the naming pattern (a random 8-character task name) recurred across
hosts and is now a detection signature. Recommend restricting SMB admin
share access from workstation subnets and disabling unconstrained scheduled
task creation for non-admin service accounts.
