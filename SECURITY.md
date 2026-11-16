# Security policy

Please report suspected vulnerabilities privately through GitHub's security
advisory feature rather than a public issue. Do not include camera credentials,
private URLs, captured media, or unredacted logs in a report.

Stream Keeper does not need camera-provider credentials. If a deployment puts
credentials in `MSE_URLS`, they may be held in process memory even though the
application does not log full URLs; remove them and rotate exposed credentials.

