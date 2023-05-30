"""
@author: Kuro
"""
from app.endpoints.routes import add_routes

add_routes()

test_item_id = ""
review_context = {"liked_review_id": test_item_id}
test_item_id = "c6a6e29e-8003-4be3-9da5-d3361be51b91"
post_context = {"post_id": test_item_id}
# paged_post_payload = mock_paged_post_data(post_context, page=1, size=10, order="asc")

# paged_payload = mock_paged_post_data(context, page=1, size=10, order="asc")
