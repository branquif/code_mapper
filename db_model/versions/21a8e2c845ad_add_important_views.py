"""add important views

Revision ID: 21a8e2c845ad
Revises: e8486fdb2ec7
Create Date: 2023-12-05 10:36:07.237456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '21a8e2c845ad'
down_revision: Union[str, None] = 'e8486fdb2ec7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQL statement to create a view
    vw_domain = sa.text("""
           CREATE VIEW VW_DOMAIN AS
           SELECT *
           FROM TB_DOMAIN
           where tb_domain.parent_code is null;
       """)
    vw_subdomain = sa.text("""
           CREATE VIEW VW_SUBDOMAIN AS
           SELECT *
           FROM TB_DOMAIN
           where TB_DOMAIN.parent_code is not null;
       """)
    op.execute(vw_domain)
    op.execute(vw_subdomain)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_domain")
    op.execute("DROP VIEW IF EXISTS vw_subdomain")

