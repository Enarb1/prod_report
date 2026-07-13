# Productivity Reporting ETL Pipeline

## Overview

This project is a small end-to-end ETL pipeline created as part of an ETL and data warehousing course.

It is inspired by a recurring weekly task from my work as a Level 1 Technical Support Team Lead: generating a productivity report from multiple data sources.

The project uses mock data only and does not contain real employee, customer, or company information.

## Data Sources

The pipeline combines:

- Phone and chat exports
- Quality reports provided by Level 2 support
- Email and daily to-do data from agent tables

The source files are stored in AWS S3.

## ETL Process

The pipeline:

1. Extracts data from AWS S3
2. Cleans and validates the datasets
3. Merges and aggregates the results
4. Loads the final report into PostgreSQL and AWS S3

It also includes a script that creates a to-do table for each new agent added to the names table.

## Project Structure

```text
prod_report/
├── config/          # Configuration and S3 utilities
├── create/          # To-do table creation
├── extract/         # Data extraction from S3
├── transform/       # Cleaning, merging, and aggregation
├── validations/     # Data-quality checks
├── load/            # Loading to PostgreSQL and S3
├── scripts/         # Pipeline execution scripts
└── notebooks/       # Data exploration
```

## Technologies
- Python
- pandas
- PostgreSQL
- AWS S3
- boto3
- SQLAlchemy
- Jupyter Notebook
- Setup

Install the dependencies:
```text
pip install -r requirements.txt
```

Create a .env file with your AWS and PostgreSQL configuration.

Do not commit credentials or sensitive information to version control.

## Run the Pipeline

```text
python scripts/get_prod_report.py
```
Generate missing agent to-do tables:

```text
python scripts/generate_todo_tables.py
```

## Purpose

This project demonstrates:

- ETL pipeline design
- Data cleaning and validation
- Multi-source data integration
- AWS S3 and PostgreSQL usage
- Automation of a recurring reporting process

## Disclaimer
This project is for educational and portfolio purposes. All data and business entities are fictional or mocked.