"""add book fields

Revision ID: xxxx
Revises: 
Create Date: 2024-12-13 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'xxxx'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create book table with all required fields
    op.create_table(
        'book',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('author', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cover_image', sa.String(length=500), nullable=True),
        sa.Column('cover_url', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=200), nullable=True),
        sa.Column('file_type', sa.String(length=20), nullable=True),
        sa.Column('total_pages', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('language', sa.String(length=20), nullable=True),
        sa.Column('accessible_without_login', sa.Boolean(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('source_id', sa.String(length=100), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('book') 