import os

import lightbulb


def _role_id_from_env(name: str) -> int | None:
    raw_value = os.getenv(name)
    if not raw_value:
        return None
    try:
        return int(raw_value)
    except ValueError:
        return None


CONTRIBUTOR_ROLE_ID = _role_id_from_env('CONTRIBUTOR_ROLE_ID')
BUILD_CONTRIBUTOR_ROLE_ID = _role_id_from_env('BUILD_CONTRIBUTOR_ROLE_ID') or CONTRIBUTOR_ROLE_ID
SALES_CONTRIBUTOR_ROLE_ID = _role_id_from_env('SALES_CONTRIBUTOR_ROLE_ID') or CONTRIBUTOR_ROLE_ID


def _role_or_owner(role_id: int | None, name: str):
    @lightbulb.hook(lightbulb.ExecutionSteps.CHECKS, skip_when_failed=True, name=name)
    async def check_role_or_owner(pipeline: lightbulb.ExecutionPipeline, ctx: lightbulb.Context) -> None:
        try:
            await lightbulb.prefab.owner_only(pipeline, ctx)
            return
        except lightbulb.prefab.NotOwner:
            pass
        if role_id and ctx.member and role_id in ctx.member.role_ids:
            return
        raise lightbulb.prefab.MissingRequiredRoles([role_id] if role_id else [])

    return check_role_or_owner


def contributor_only():
    """Check for contributor role or owner."""
    return _role_or_owner(CONTRIBUTOR_ROLE_ID, "contributor_only")


def build_contributor_only():
    """Check for build contributor role or owner."""
    return _role_or_owner(BUILD_CONTRIBUTOR_ROLE_ID, "build_contributor_only")


def sales_contributor_only():
    """Check for sales contributor role or owner."""
    return _role_or_owner(SALES_CONTRIBUTOR_ROLE_ID, "sales_contributor_only")

