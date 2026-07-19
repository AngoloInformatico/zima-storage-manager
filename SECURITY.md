# Security Policy

ZSM performs privileged storage metadata operations. Run only releases you reviewed and obtained from a trusted source.

Report vulnerabilities privately to the repository maintainer. Do not include personal data, credentials, disk contents or complete system logs in public issues.

ZSM never formats disks, changes partitions, removes user data or executes shell strings. Commands are invoked as argument arrays. Database changes are parameterized and wrapped in transactions.
