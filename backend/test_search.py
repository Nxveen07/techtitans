import sys
import os

# Add the current directory to sys.path to import services
sys.path.append(os.getcwd())

from services.video_service import get_video_content

# Test with the Bing URL from the user's image
test_url = "https://www.bing.com/videos/riverview/relatedvideo?q=youtube+news&&mid=4546DC3AB90C377B21334546DC3AB90C377B2133&FORM=VCGVRP"
print(f"Testing URL: {test_url}")
result = get_video_content(test_url)

print("\n--- Detection Result ---")
print(f"Platform: {result.get('platform')}")
print(f"Metadata: {result.get('metadata')}")

print("\n--- Processed Text (First 300 chars) ---")
print(result['text'][:300])

if "SEARCH RESULT TOPIC: youtube news" in result['text']:
    print("\nSUCCESS: Search query 'youtube news' was correctly extracted!")
else:
    print("\nFAILURE: Search query not found in processed text.")
