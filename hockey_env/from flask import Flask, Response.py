from flask import Flask, Response
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Proxy route
@app.route('/proxy-feed', methods=['GET'])
def proxy_feed():
    # Original feed URL
    original_feed_url = "https://feeds.feedburner.com/simplecast/v0e9L7Sacoa"
    new_email = "tapetotapemk@gmail.com"  # The new email address
    
    try:
        # Fetch the original RSS feed
        response = requests.get(original_feed_url)
        response.raise_for_status()  # Check for request errors

        # Parse the XML content
        soup = BeautifulSoup(response.content, 'xml')

        # Find the <author> tag and modify its content
        author_tag = soup.find('author')
        if author_tag and 'admin@bleav.com' in author_tag.text:
            # Replace the old email address with the new one
            author_tag.string = author_tag.text.replace('admin@bleav.com', new_email)

        # Convert the modified feed back to XML
        modified_feed = str(soup)

        # Serve the modified feed as XML
        return Response(modified_feed, content_type='application/rss+xml')

    except Exception as e:
        return Response(f"Error: {e}", status=500)

# Run the server (for local testing)
if __name__ == '__main__':
    app.run(debug=True)
