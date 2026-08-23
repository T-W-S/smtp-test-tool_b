from __future__ import annotations

import re


EMAIL_MAX_LENGTH = 254
LOCAL_PART_MAX_LENGTH = 64
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def validate_email(email: str) -> bool:
    email = email.strip()

    if not email:
        raise ValueError("Email address cannot be empty")

    if len(email) > EMAIL_MAX_LENGTH:
        raise ValueError("Email address is too long")

    if not EMAIL_PATTERN.match(email):
        raise ValueError("Email address format is invalid")

    try:
        local_part, domain = email.rsplit('@', 1)
    except ValueError:
        raise ValueError("Email address must contain exactly one @ symbol")

    if len(local_part) > LOCAL_PART_MAX_LENGTH:
        raise ValueError("Local part of email address is too long")

    if '..' in local_part or '..' in domain:
        raise ValueError("Email address cannot contain consecutive dots")

    if '.' not in domain:
        raise ValueError("Domain must contain at least one dot")

    return True
