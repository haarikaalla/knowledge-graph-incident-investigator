---
id: incident_0003
synthetic: true
date: 2026-06-19
technique_ids: [T1546.013]
severity: medium
---

# Incident 0003: Persistence via malicious PowerShell profile

A workstation in the engineering department repeatedly re-established a
beacon connection to an external IP even after the initial dropper was
removed by antivirus. Root cause was a modified PowerShell profile script
(profile.ps1) that silently re-downloaded and executed a loader every time
a new PowerShell session opened (T1546.013 - PowerShell Profile). The
profile had been modified nine days before detection, meaning the beacon
had persisted through two full antivirus scans and one reboot. Detection
finally triggered on outbound traffic to a domain that had recently been
added to a threat intel blocklist, not on the persistence mechanism itself.

Lessons: standard AV did not flag the profile modification because it is a
legitimate, commonly-used file. Recommend baselining PowerShell profile
hashes across the fleet and alerting on any modification outside change
management windows.
