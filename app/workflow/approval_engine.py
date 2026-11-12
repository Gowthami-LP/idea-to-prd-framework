AUTHORIZED_APPROVER_ROLES = {
    "SPONSOR",
    "PRODUCT_OWNER",
    "EXECUTIVE",
}


def validate_approver(role: str) -> None:
    if role not in AUTHORIZED_APPROVER_ROLES:
        raise PermissionError("Approver is not authorized")
