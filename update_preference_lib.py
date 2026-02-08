#!/usr/bin/env python3
"""
FashionXG Preference Library Updater
Fetches designer feedback and builds preference profile for filtering
"""

import os
import json
import requests
from collections import Counter
from pathlib import Path
import logging
from typing import Dict, List

# Configuration
SERVER_URL = os.getenv("FASHIONXG_SERVER", "https://design.chermz112.xyz")
PREFERENCE_FILE = "preference_profile.json"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PreferenceLibraryBuilder:
    """Build preference profile from designer feedback"""

    def __init__(self, server_url: str = SERVER_URL):
        self.server_url = server_url
        self.liked_images = []
        self.disliked_images = []

    def fetch_feedback_data(self) -> Dict:
        """Fetch all images with designer ratings from server"""
        try:
            # Fetch liked images (designer_rating = 1)
            response_liked = requests.get(
                f"{self.server_url}/api/images/processed",
                params={"designer_rating": 1},
                timeout=30
            )
            response_liked.raise_for_status()
            self.liked_images = response_liked.json()

            # Fetch disliked images (designer_rating = -1)
            response_disliked = requests.get(
                f"{self.server_url}/api/images/processed",
                params={"designer_rating": -1},
                timeout=30
            )
            response_disliked.raise_for_status()
            self.disliked_images = response_disliked.json()

            logger.info(f"Fetched {len(self.liked_images)} liked and {len(self.disliked_images)} disliked images")
            return {
                "liked": self.liked_images,
                "disliked": self.disliked_images
            }

        except Exception as e:
            logger.error(f"Failed to fetch feedback data: {e}")
            return {"liked": [], "disliked": []}

    def extract_tag_frequencies(self, images: List[Dict]) -> Dict[str, int]:
        """Extract and count tag frequencies from images"""
        tag_counter = Counter()

        for image in images:
            # Get tags from tags_list field
            tags = image.get("tags_list", [])
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = []

            # Also check fashion_tags
            fashion_tags = image.get("fashion_tags", {})
            if isinstance(fashion_tags, str):
                try:
                    fashion_tags = json.loads(fashion_tags)
                except:
                    fashion_tags = {}

            # Count all tags
            for tag in tags:
                tag_counter[tag.lower()] += 1

            # Count fashion category tags
            if isinstance(fashion_tags, dict):
                for category, category_tags in fashion_tags.items():
                    if isinstance(category_tags, list):
                        for tag in category_tags:
                            tag_counter[tag.lower()] += 1

        return dict(tag_counter)

    def extract_clip_vectors(self, images: List[Dict]) -> List[List[float]]:
        """Extract CLIP vectors from images (if available)"""
        vectors = []

        for image in images:
            # Check if image has CLIP vector stored
            vector = image.get("clip_vector")
            if vector:
                if isinstance(vector, str):
                    try:
                        vector = json.loads(vector)
                    except:
                        continue
                vectors.append(vector)

        logger.info(f"Extracted {len(vectors)} CLIP vectors")
        return vectors

    def build_preference_profile(self) -> Dict:
        """Build complete preference profile"""
        # Fetch data
        feedback_data = self.fetch_feedback_data()

        if not feedback_data["liked"] and not feedback_data["disliked"]:
            logger.warning("No feedback data available, creating empty profile")
            return {
                "liked_tags": [],
                "disliked_tags": [],
                "liked_tag_frequencies": {},
                "disliked_tag_frequencies": {},
                "liked_vectors": [],
                "total_liked": 0,
                "total_disliked": 0
            }

        # Extract tag frequencies
        liked_tag_freq = self.extract_tag_frequencies(feedback_data["liked"])
        disliked_tag_freq = self.extract_tag_frequencies(feedback_data["disliked"])

        # Get top tags
        liked_tags = [tag for tag, _ in sorted(liked_tag_freq.items(), key=lambda x: x[1], reverse=True)]
        disliked_tags = [tag for tag, _ in sorted(disliked_tag_freq.items(), key=lambda x: x[1], reverse=True)]

        # Extract CLIP vectors
        liked_vectors = self.extract_clip_vectors(feedback_data["liked"])

        # Build profile
        profile = {
            "liked_tags": liked_tags[:50],  # Top 50 liked tags
            "disliked_tags": disliked_tags[:50],  # Top 50 disliked tags
            "liked_tag_frequencies": liked_tag_freq,
            "disliked_tag_frequencies": disliked_tag_freq,
            "liked_vectors": liked_vectors,
            "total_liked": len(feedback_data["liked"]),
            "total_disliked": len(feedback_data["disliked"]),
            "updated_at": None  # Will be set when saving
        }

        return profile

    def save_profile(self, profile: Dict):
        """Save preference profile to file"""
        from datetime import datetime

        profile["updated_at"] = datetime.now().isoformat()

        with open(PREFERENCE_FILE, 'w') as f:
            json.dump(profile, f, indent=2)

        logger.info(f"Saved preference profile to {PREFERENCE_FILE}")

    def print_summary(self, profile: Dict):
        """Print summary of preference profile"""
        print("\n" + "="*60)
        print("PREFERENCE PROFILE SUMMARY")
        print("="*60)
        print(f"Total Liked Images: {profile['total_liked']}")
        print(f"Total Disliked Images: {profile['total_disliked']}")
        print(f"\nTop 10 Liked Tags:")
        for i, tag in enumerate(profile['liked_tags'][:10], 1):
            freq = profile['liked_tag_frequencies'].get(tag, 0)
            print(f"  {i}. {tag} ({freq} occurrences)")

        print(f"\nTop 10 Disliked Tags:")
        for i, tag in enumerate(profile['disliked_tags'][:10], 1):
            freq = profile['disliked_tag_frequencies'].get(tag, 0)
            print(f"  {i}. {tag} ({freq} occurrences)")

        print(f"\nCLIP Vectors: {len(profile['liked_vectors'])} available")
        print("="*60 + "\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Update FashionXG Preference Library")
    parser.add_argument("--server", type=str, default=SERVER_URL, help="Server URL")
    parser.add_argument("--output", type=str, default=PREFERENCE_FILE, help="Output file path")

    args = parser.parse_args()

    # Update global config
    global SERVER_URL, PREFERENCE_FILE
    SERVER_URL = args.server
    PREFERENCE_FILE = args.output

    # Build preference library
    builder = PreferenceLibraryBuilder(SERVER_URL)
    profile = builder.build_preference_profile()

    # Save profile
    builder.save_profile(profile)

    # Print summary
    builder.print_summary(profile)

    logger.info("Preference library update complete!")


if __name__ == "__main__":
    main()
