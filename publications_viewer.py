"""
Publications Viewer
===================

This script demonstrates how to read and display the saved publications
from the Telegram News Agent. It shows how to work with the JSON database
and provides examples of data analysis.
"""

import json
import os
from datetime import datetime

def load_publications():
    """Load publications from the JSON database"""
    json_file = os.path.join("publications", "news_database.json")
    
    if not os.path.exists(json_file):
        print("❌ No publications found. Run the agent first to collect some articles.")
        return []
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️  Error reading publications database")
        return []

def display_publications_summary(publications):
    """Display a summary of all publications"""
    if not publications:
        print("📭 No publications in database")
        return
    
    print(f"\n📊 PUBLICATIONS SUMMARY")
    print("=" * 50)
    print(f"Total Articles: {len(publications)}")
    
    # Count by date
    dates = {}
    authors = {}
    
    for pub in publications:
        date = pub.get('date_extracted', 'Unknown')
        author = pub.get('author', 'Unknown')
        
        dates[date] = dates.get(date, 0) + 1
        authors[author] = authors.get(author, 0) + 1
    
    print(f"\nArticles by Date:")
    for date in sorted(dates.keys(), reverse=True):
        print(f"  {date}: {dates[date]} articles")
    
    print(f"\nTop Authors:")
    sorted_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]
    for author, count in sorted_authors:
        print(f"  {author}: {count} articles")

def display_recent_articles(publications, limit=5):
    """Display the most recent articles"""
    if not publications:
        return
    
    print(f"\n📰 RECENT ARTICLES (Last {limit})")
    print("=" * 50)
    
    # Sort by date_extracted and time_extracted
    sorted_pubs = sorted(publications, 
                        key=lambda x: (x.get('date_extracted', ''), x.get('time_extracted', '')), 
                        reverse=True)
    
    for i, pub in enumerate(sorted_pubs[:limit], 1):
        print(f"\n{i}. {pub.get('title', 'No Title')[:60]}...")
        print(f"   Author: {pub.get('author', 'Unknown')}")
        print(f"   Date: {pub.get('date_extracted', 'Unknown')} {pub.get('time_extracted', 'Unknown')}")
        print(f"   URL: {pub.get('url', 'No URL')}")

def search_publications(publications, search_term):
    """Search publications by title or summary"""
    if not publications:
        return []
    
    search_term = search_term.lower()
    results = []
    
    for pub in publications:
        title = pub.get('title', '').lower()
        summary = pub.get('summary', '').lower()
        
        if search_term in title or search_term in summary:
            results.append(pub)
    
    return results

def display_search_results(results, search_term):
    """Display search results"""
    print(f"\n🔍 SEARCH RESULTS FOR '{search_term}'")
    print("=" * 50)
    
    if not results:
        print("No articles found matching your search term")
        return
    
    print(f"Found {len(results)} articles:")
    
    for i, pub in enumerate(results, 1):
        print(f"\n{i}. {pub.get('title', 'No Title')}")
        print(f"   Summary: {pub.get('summary', 'No Summary')[:100]}...")
        print(f"   Author: {pub.get('author', 'Unknown')}")
        print(f"   Date: {pub.get('date_extracted', 'Unknown')}")

def export_to_text(publications, filename="publications_export.txt"):
    """Export all publications to a text file"""
    if not publications:
        print("No publications to export")
        return
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("TELEGRAM NEWS AGENT - PUBLICATIONS EXPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Articles: {len(publications)}\n\n")
            
            for i, pub in enumerate(publications, 1):
                f.write(f"{i}. {pub.get('title', 'No Title')}\n")
                f.write(f"   Author: {pub.get('author', 'Unknown')}\n")
                f.write(f"   Date: {pub.get('date_extracted', 'Unknown')} {pub.get('time_extracted', 'Unknown')}\n")
                f.write(f"   URL: {pub.get('url', 'No URL')}\n")
                f.write(f"   Summary: {pub.get('summary', 'No Summary')}\n")
                f.write(f"   Image: {pub.get('image', 'No Image')}\n")
                f.write("-" * 80 + "\n\n")
        
        print(f"✅ Exported {len(publications)} articles to {filename}")
        
    except Exception as e:
        print(f"❌ Error exporting: {e}")

def main():
    """Main function with interactive menu"""
    print("📖 PUBLICATIONS VIEWER")
    print("=" * 30)
    
    # Load publications
    publications = load_publications()
    
    while True:
        print("\n📋 MENU:")
        print("1. Show summary")
        print("2. Show recent articles")
        print("3. Search articles")
        print("4. Export to text file")
        print("5. Reload data")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            display_publications_summary(publications)
            
        elif choice == "2":
            try:
                limit = int(input("How many recent articles to show? (default 5): ") or "5")
                display_recent_articles(publications, limit)
            except ValueError:
                display_recent_articles(publications)
                
        elif choice == "3":
            search_term = input("Enter search term: ").strip()
            if search_term:
                results = search_publications(publications, search_term)
                display_search_results(results, search_term)
            else:
                print("Please enter a search term")
                
        elif choice == "4":
            filename = input("Export filename (default: publications_export.txt): ").strip()
            if not filename:
                filename = "publications_export.txt"
            export_to_text(publications, filename)
            
        elif choice == "5":
            publications = load_publications()
            print("✅ Data reloaded")
            
        elif choice == "6":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid option, please select 1-6")

if __name__ == "__main__":
    main()