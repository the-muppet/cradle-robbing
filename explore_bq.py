from google.cloud import bigquery
import os
from pprint import pprint
import inquirer
import pandas as pd

def initialize_client():
    # Set up credentials
    credentials = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'creds.json')
    
    # Create the client
    client = bigquery.Client()
    
    return client

def explore_bigquery():
    while True:
        client = initialize_client()
        
        print("\n=== Available Datasets ===")
        datasets = list(client.list_datasets())
        
        if datasets:
            dataset_choices = [dataset.dataset_id for dataset in datasets]
            dataset_choices.append("Exit")
            
            questions = [
                inquirer.List(
                    "dataset_id",
                    message="Select a dataset to explore (or exit):",
                    choices=dataset_choices,
                ),
            ]
            
            answers = inquirer.prompt(questions)
            selected_dataset_id = answers["dataset_id"]
            
            if selected_dataset_id == "Exit":
                print("Exiting the script...")
                break
            else:
                explore_dataset(selected_dataset_id)
        else:
            print("No datasets found")
            break

def explore_dataset(dataset_id):
    while True:
        client = initialize_client()
        
        dataset = client.get_dataset(dataset_id)

        print(f"\n=== Tables in Dataset: {dataset_id} ===")
        tables = list(client.list_tables(dataset))

        if tables:
            table_choices = [table.table_id for table in tables]
            table_choices.append("Back to Datasets")
            
            questions = [
                inquirer.List(
                    "table_id",
                    message="Select a table to explore (or go back to datasets):",
                    choices=table_choices,
                    carousel=True,
                ),
            ]
            
            answers = inquirer.prompt(questions)
            selected_table_id = answers["table_id"]
            
            if selected_table_id == "Back to Datasets":
                break
            else:
                explore_table(dataset_id, selected_table_id)
        else:
            print("No tables found in the dataset")
            input("Press Enter to go back to datasets...")
            break

def explore_table(dataset_id, table_id):
    client = initialize_client()
    
    table_ref = client.dataset(dataset_id).table(table_id)
    table = client.get_table(table_ref)
    
    print(f"\nTable: {dataset_id}.{table_id}")
    print(f"Row count: {table.num_rows}")
    print("Schema:")
    for field in table.schema:
        print(f"- {field.name} ({field.field_type})")
    
    print("\nPreview of the first 5 rows:")
    query = f"SELECT * FROM `{dataset_id}.{table_id}` LIMIT 5"
    query_job = client.query(query)
    results = query_job.result()
    
    for row in results:
        print(dict(row))
    
    questions = [
        inquirer.Confirm(
            "download",
            message="Do you want to download this table as a CSV file?",
            default=False,
        ),
    ]
    
    answers = inquirer.prompt(questions)
    
    if answers["download"]:
        print("\nDownloading table as CSV...")
        query = f"SELECT * FROM `{dataset_id}.{table_id}`"
        df = client.query(query).to_dataframe()
        df.to_csv(f"{table_id}.csv", index=False)
        print(f"Table downloaded as {table_id}.csv")
    else:
        print("Download cancelled.")

if __name__ == "__main__":
    explore_bigquery()
