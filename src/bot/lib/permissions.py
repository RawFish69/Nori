"""Permission checks for commands."""

import lightbulb
import os

CONTRIBUTOR_ROLE_ID = int(os.getenv('CONTRIBUTOR_ROLE_ID', '0')) if os.getenv('CONTRIBUTOR_ROLE_ID') else None
BUILD_CONTRIBUTOR_ROLE_ID = int(os.getenv('BUILD_CONTRIBUTOR_ROLE_ID', '0')) if os.getenv('BUILD_CONTRIBUTOR_ROLE_ID') else None
SALES_CONTRIBUTOR_ROLE_ID = int(os.getenv('SALES_CONTRIBUTOR_ROLE_ID', '0')) if os.getenv('SALES_CONTRIBUTOR_ROLE_ID') else None


def contributor_only():
    """Check for contributor role or owner."""
    if CONTRIBUTOR_ROLE_ID:
        return lightbulb.has_roles(CONTRIBUTOR_ROLE_ID) | lightbulb.owner_only
    return lightbulb.owner_only


def build_contributor_only():
    """Check for build contributor role or owner."""
    if BUILD_CONTRIBUTOR_ROLE_ID:
        return lightbulb.has_roles(BUILD_CONTRIBUTOR_ROLE_ID) | lightbulb.owner_only
    return lightbulb.owner_only


def sales_contributor_only():
    """Check for sales contributor role or owner."""
    if SALES_CONTRIBUTOR_ROLE_ID:
        return lightbulb.has_roles(SALES_CONTRIBUTOR_ROLE_ID) | lightbulb.owner_only
    return lightbulb.owner_only

