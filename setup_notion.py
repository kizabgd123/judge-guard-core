#!/usr/bin/env python3
"""
Notion Setup - Create Database via API
=======================================
Creates the Agent Taming Research database in Notion.

Usage:
    python3 setup_notion.py --create    # Create database
    python3 setup_notion.py --list      # List all databases
    python3 setup_notion.py --test      # Test sync
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")

if not NOTION_TOKEN:
    print("❌ NOTION_TOKEN not found in .env")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


def create_database():
    """Create a new database in Notion."""
    # First, get the user's workspace to create the database in
    # We need to create it as a child of a page
    
    # Search for a suitable parent page
    search_response = requests.post(
        "https://api.notion.com/v1/search",
        headers=HEADERS,
        json={
            "filter": {"property": "object", "value": "page"},
            "page_size": 1
        }
    )
    
    if search_response.status_code != 200:
        print(f"❌ Search failed: {search_response.text}")
        return None
    
    pages = search_response.json().get("results", [])
    if not pages:
        print("❌ No pages found. Please create at least one page in Notion first.")
        return None
    
    parent_page_id = pages[0]["id"]
    print(f"📄 Using parent page: {pages[0].get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'Untitled')}")
    
    # Create the database
    db_data = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [
            {
                "type": "text",
                "text": {"content": "Agent Taming Research Pipeline"}
            }
        ],
        "properties": {
            "Action": {"title": {}},
            "Details": {"rich_text": {}},
            "Timestamp": {"date": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Done", "color": "green"},
                        {"name": "In Progress", "color": "yellow"},
                        {"name": "Error", "color": "red"}
                    ]
                }
            }
        }
    }
    
    response = requests.post(
        "https://api.notion.com/v1/databases",
        headers=HEADERS,
        json=db_data
    )
    
    if response.status_code == 200:
        db = response.json()
        db_id = db["id"]
        print(f"✅ Database created!")
        print(f"📊 Database ID: {db_id}")
        print(f"🔗 URL: {db.get('url', 'N/A')}")
        
        # Save to .env
        with open(".env", "a") as f:
            f.write(f"\nNOTION_DATABASE_ID={db_id}\n")
        
        print("✅ Database ID added to .env")
        return db_id
    else:
        print(f"❌ Failed to create database: {response.status_code}")
        print(response.text)
        return None


def list_databases():
    """List all databases the integration has access to."""
    response = requests.post(
        "https://api.notion.com/v1/search",
        headers=HEADERS,
        json={
            "filter": {"property": "object", "value": "database"},
            "page_size": 10
        }
    )
    
    if response.status_code == 200:
        databases = response.json().get("results", [])
        print(f"📊 Found {len(databases)} database(s):")
        for db in databases:
            title_array = db.get("title", [])
            if title_array:
                title = title_array[0].get("plain_text", "Untitled")
            else:
                title = "Untitled"
            db_id = db["id"]
            print(f"  - {title} (ID: {db_id})")
        return databases
    else:
        print(f"❌ Failed to list databases: {response.status_code}")
        print(response.text)
        return []


def test_sync():
    """Test syncing an entry to Notion."""
    db_id = os.getenv("NOTION_DATABASE_ID")
    if not db_id:
        print("❌ NOTION_DATABASE_ID not set. Run --create first.")
        return
    
    # Create a test entry
    entry_data = {
        "parent": {"database_id": db_id},
        "properties": {
            "Action": {"title": [{"text": {"content": "Test Entry"}}]},
            "Details": {"rich_text": [{"text": {"content": "Testing Notion integration from Python"}}]},
            "Timestamp": {"date": {"start": "2026-01-16T22:07:00Z"}},
            "Status": {"select": {"name": "Done"}}
        }
    }
    
    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json=entry_data
    )
    
    if response.status_code == 200:
        page = response.json()
        print(f"✅ Test entry created!")
        print(f"🔗 URL: {page.get('url', 'N/A')}")
    else:
        print(f"❌ Failed to create test entry: {response.status_code}")
        print(response.text)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Notion Setup")
    parser.add_argument("--create", action="store_true", help="Create database")
    parser.add_argument("--list", action="store_true", help="List databases")
    parser.add_argument("--test", action="store_true", help="Test sync")
    
    args = parser.parse_args()
    
    if args.create:
        create_database()
    elif args.list:
        list_databases()
    elif args.test:
        test_sync()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
