from selectolax.parser import HTMLParser

def extract_article(html): 
    """extracting title and text from HTML"""

    def extract_article(html):
        tree = HTMLParser(html)
        title = tree.css_first("h1").text() if tree.css_first("h1") else "No Title"
        paragraphs = [p.text() for p in tree.css("p")]
        content = "\n".join(paragraphs)
        return {"title": title, "content": content}