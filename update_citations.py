import json
from scholarly import scholarly

def get_citations(user_id):
    try: 
        author = scholarly.search_author_id(user_id) 
        author = scholarly.fill(author, sections=['counts']) 
        return str(author.get('citedby', 0))
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None
 
user_id = 'JlNb4R8AAAAJ'
count = get_citations(user_id)

if count:
    with open('citations.json', 'w', encoding='utf-8') as f:
        json.dump({'citations': count}, f, ensure_ascii=False, indent=2)
    print(f"Successfully updated: {count}")
else:
    print("Failed to retrieve citations.")
    import sys
    sys.exit(1)