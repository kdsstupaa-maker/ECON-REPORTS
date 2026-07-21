import feedparser
import logging
import urllib.parse
from datetime import datetime, timedelta
import time
import uuid

logger = logging.getLogger(__name__)

class RSSCrawler:
    def __init__(self, target_days=3):
        self.target_days = target_days
        # Some generic known RSS patterns
        self.rss_suffixes = ["/rss", "/feed", "/rss.xml", "/feed.xml"]

    def fetch_feeds(self, institutions):
        """
        institutions: list of dicts [{'name': '...', 'url': '...'}]
        returns: list of reports
        """
        cutoff_date = datetime.now() - timedelta(days=self.target_days)
        reports = []

        for inst in institutions:
            name = inst['name']
            base_url = inst['url']
            
            # This is a best-effort approach to find RSS feeds automatically if they are not explicitly known.
            # In production, explicit RSS URLs should be mapped per institution.
            success = False
            for suffix in self.rss_suffixes:
                if success:
                    break
                
                feed_url = urllib.parse.urljoin(base_url, suffix)
                logger.info(f"Trying to fetch RSS for {name} from {feed_url}")
                try:
                    feed = feedparser.parse(feed_url)
                    if not feed.entries:
                        continue
                        
                    for entry in feed.entries:
                        # Extract date
                        published = entry.get('published_parsed') or entry.get('updated_parsed')
                        if published:
                            dt = datetime.fromtimestamp(time.mktime(published))
                            if dt < cutoff_date:
                                continue
                            date_str = dt.strftime("%Y-%m-%d")
                        else:
                            date_str = datetime.now().strftime("%Y-%m-%d")

                        title = entry.get('title', 'No Title')
                        link = entry.get('link', '')
                        author = entry.get('author', name)
                        
                        summary = entry.get('summary', '')
                        
                        reports.append({
                            "key": f"rss_{uuid.uuid4().hex[:8]}",
                            "name": name,
                            "title": title,
                            "pdf_url": link,  # Fallback to link if PDF is not available in RSS
                            "author": author,
                            "date": date_str,
                            "summary_data": {
                                "title": title,
                                "summary": [summary[:200] + "..."] if summary else ["(내용 없음)"],
                                "implication": {"upside_risk": "-", "downside_risk": "-"},
                                "keywords": ["RSS 수집"]
                            }
                        })
                    success = True
                    logger.info(f"Successfully fetched {len(feed.entries)} entries from {feed_url} for {name}")
                except Exception as e:
                    logger.warning(f"Failed to parse RSS {feed_url}: {e}")
                    
        return reports
