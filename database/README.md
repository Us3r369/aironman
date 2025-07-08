# Database Setup

This directory contains the raw SQL schema and seeding logic for the AIronman endurance training app.

## How it works
- On container startup, the SQL script in `init/001_create_schema.sql` is automatically run by the official PostgreSQL Docker image.
- The schema is based on `reference_files/endurance_training_schema.md`.
- Database credentials and config are set via environment variables (see `.env.example`).

## Seeding
- The script `database/seed_data.py` will:
  - Create a user named Jan with a random UUID (if not present)
  - Parse `data/athlete_profile/profile.json` and insert it into the `athlete_profile` table
- This script is run as a one-off service in Docker Compose (see below).

## Updating the Schema
- To make changes, edit or add SQL files in `database/init/`.
- Restart the database container to re-run the scripts (note: this will only run on a fresh DB unless you manually drop/recreate tables).

## Environment Variables
- See `.env.example` for required variables:
  - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`

## Migrations
- For production or evolving schemas, consider using Alembic or a similar migration tool in the future. 