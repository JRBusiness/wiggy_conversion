import operator
import time
import spacy
from atlassian import Confluence
from settings import Config as settings


class PageGroupper:
    """
    This class is used to group pages based on title relevance to body content
    """

    def __init__(self):
        self.conf = Confluence(
            url=settings.jira_org,
            username=settings.jira_user,
            password=settings.jira_key,
        )
        self.space_key = "~6400fa9a0a4a47fb8d21fd26"
        self.nlp = spacy.load("en_core_web_lg")
        self.all_pages = self.conf.get_all_pages_from_space(
            self.space_key, expand="body.storage.value"
        )

    # Define function to weigh the similarity of two pieces of text
    def weigh_similarity(self, text1, text2):
        """
        It takes two strings, converts them to spaCy documents, and then returns the similarity between them

        :param text1: The first text to be compared
        :param text2: The second text to compare to the first
        :return: The similarity between the two texts.
        """
        doc1 = self.nlp(text1)
        doc2 = self.nlp(text2)
        return doc1.similarity(doc2)

    # Define function to group pages based on title relevance to body content

    def group_pages_by_title_relevance(self, pages):
        """
        It groups pages with similar body content, and then sorts each group by title relevance to body content

        :param pages: A list of pages to group
        """

        # Group pages with similar body content
        page_groups = []
        while pages:
            page = pages.pop(0)
            page_title = page["title"]
            page_body = page["body"]["storage"]["value"]
            group = [page]
            for i, other_page in enumerate(pages):
                other_page_title = other_page["title"]
                other_page_body = other_page["body"]["storage"]["value"]
                similarity = self.weigh_similarity(page_body, other_page_body)
                if similarity >= 0.9:
                    group.append(other_page)
                    del pages[i]
            page_groups.append((page_title, group))
        # Sort each group by title relevance to body content
        for title, group in page_groups:
            weights = [
                (page["title"], self.weigh_similarity(title, page["title"]))
                for page in group
            ]
            weights.sort(key=operator.itemgetter(1), reverse=True)
            group_titles = [title] + [title for title, weight in weights]
            # Choose the most descriptive title as the page they group on
            group_title = max(group_titles, key=lambda _title: len(_title.split()))
            yield group_title, group

    # Define function to create page groups in Confluence
    def create_page_groups(self):
        """
        It creates a page group for each group of pages that have a similar title, and moves the pages into the page group
        """
        # Get all pages in the space
        pages = list(self.all_pages)
        # Group pages by title relevance to body content
        grouped_pages = self.group_pages_by_title_relevance(pages)
        # Create page groups in Confluence
        for group_title, group_pages in grouped_pages:
            parent_id = next(
                (page["id"] for page in pages if page["title"] == group_title),
                None,
            )
            # Create the new page group
            new_group_data = {
                "title": f"{group_title} Group",
                "type": "page",
                "body": {
                    "storage": {
                        "value": f'<ac:link><ri:page ri:content-title="{group_title}" ri:space-key="{self.space_key}"/></ac:link>'
                    },
                    "representation": "storage",
                },
            }
            new_group = self.conf.create_page(space=self.space_key, **new_group_data)
            print(f"Page group {new_group['title']} has been created.")
            # Move the group pages to the new page group
            for page in group_pages:
                self.conf.move_page(page["id"], new_group["id"])
                print(f"Page {page['title']} has been moved to {new_group['title']}.")
            # Move the new page group to the parent page
            if parent_id:
                self.conf.move_page(new_group["id"], parent_id)
                print(
                    f"Page group {new_group['title']} has been moved to {group_title}."
                )


PageGroupper().create_page_groups()
