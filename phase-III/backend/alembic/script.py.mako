"""
Alembic migration script template.

This template is used to generate new migration files.
Each migration represents a single schema change.
"""

"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """Apply schema changes to upgrade database."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Reverse schema changes to downgrade database."""
    ${downgrades if downgrades else "pass"}
