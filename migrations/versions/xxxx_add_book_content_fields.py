"""add book content fields

Revision ID: xxxx
Revises: previous_revision
Create Date: 2024-xx-xx

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add new columns to books table
    op.add_column('books', sa.Column('content', sa.Text(), nullable=True))
    op.add_column('books', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('books', sa.Column('source_url', sa.String(500), nullable=True))
    op.add_column('books', sa.Column('file_path', sa.String(500), nullable=True))
    op.add_column('books', sa.Column('updated_at', sa.DateTime(), nullable=True))

def downgrade():
    # Remove the new columns
    op.drop_column('books', 'content')
    op.drop_column('books', 'summary')
    op.drop_column('books', 'source_url')
    op.drop_column('books', 'file_path')
    op.drop_column('books', 'updated_at') 