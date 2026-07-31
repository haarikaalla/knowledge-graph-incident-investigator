---
id: incident_0001
synthetic: true
date: 2026-03-14
technique_ids: [T1566.002, T1078]
severity: high
---

# Incident 0001: Credential theft via spearphishing link

A finance team employee clicked a link in an email impersonating the company's
expense system. The link led to a credential-harvesting page that mimicked the
real SSO login screen (T1566.002 - Spearphishing Link). Captured credentials
were used four hours later to log into the corporate VPN from an unfamiliar
IP address in a different country, then to authenticate to the internal
finance SharePoint site using the stolen but otherwise valid account
(T1078 - Valid Accounts). No malware was dropped; the actor relied entirely
on legitimate access. Access was revoked and the password rotated within 40
minutes of the anomalous login being flagged by geo-velocity detection.

Lessons: geo-velocity alerting caught this quickly, but the initial email
bypassed the spam filter because it was sent from a newly registered
look-alike domain. Recommend DMARC enforcement review and MFA on the SSO
login itself, not just the VPN.
