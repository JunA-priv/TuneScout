import requests
from bs4 import BeautifulSoup

def scrape_schedule():
    url = "https://9spices.rinky.info/schedule/?sch-year=2025&sch-mon=07"
    
    response = requests.get(url)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all parent elements with class "sch-actlist"
    parent_elements = soup.find_all('div', class_='sch-actlist')
    
    results = []
    for parent in parent_elements:
        # Find all child elements with class "actlist-name-p"
        child_elements = parent.find_all('p', class_='actlist-name-p')
        
        for child in child_elements:
            results.append(child.get_text(strip=True))
    
    return results

if __name__ == "__main__":
    data = scrape_schedule()
    for item in data:
        print(item)