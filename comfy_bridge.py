#!/usr/bin/env python3
"""
FashionXG ComfyUI Bridge Script
Connects cloud server with local Mac ComfyUI for AI tagging
"""

import os
import json
import time
import requests
import websocket
import uuid
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Configuration
SERVER_URL = os.getenv("FASHIONXG_SERVER", "https://design.chermz112.xyz")
COMFYUI_URL = "http://127.0.0.1:8188"
WORKFLOW_PATH = "fashion_tagger_api.json"
TEMP_DIR = Path("./temp_images")
PREFERENCE_FILE = "preference_profile.json"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comfy_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Blacklist tags that should be filtered out
BLACKLIST_TAGS = {'text', 'watermark', 'meme', 'blurry', 'low_quality', 'screenshot'}


class ComfyUIClient:
    """Client for interacting with ComfyUI API"""

    def __init__(self, server_address: str = COMFYUI_URL):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())

    def queue_prompt(self, prompt: Dict) -> str:
        """Queue a prompt to ComfyUI and return the prompt_id"""
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(f"{self.server_address}/prompt", data=data)
        response = json.loads(urllib.request.urlopen(req).read())
        return response['prompt_id']

    def get_image(self, filename: str, subfolder: str, folder_type: str) -> bytes:
        """Get image data from ComfyUI output"""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(f"{self.server_address}/view?{url_values}") as response:
            return response.read()

    def get_history(self, prompt_id: str) -> Dict:
        """Get execution history for a prompt"""
        with urllib.request.urlopen(f"{self.server_address}/history/{prompt_id}") as response:
            return json.loads(response.read())

    def track_progress(self, prompt_id: str, timeout: int = 300) -> Dict:
        """Track prompt execution via WebSocket"""
        ws = websocket.WebSocket()
        ws.connect(f"ws://{self.server_address.split('://')[-1]}/ws?clientId={self.client_id}")

        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                ws.close()
                raise TimeoutError(f"Prompt {prompt_id} timed out after {timeout}s")

            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        ws.close()
                        return self.get_history(prompt_id)[prompt_id]

        ws.close()
        return {}


class FashionXGBridge:
    """Main bridge between server and ComfyUI"""

    def __init__(self):
        self.comfy_client = ComfyUIClient()
        self.workflow = self.load_workflow()
        self.preferences = self.load_preferences()
        TEMP_DIR.mkdir(exist_ok=True)

    def load_workflow(self) -> Dict:
        """Load ComfyUI workflow from JSON file"""
        if not Path(WORKFLOW_PATH).exists():
            logger.error(f"Workflow file not found: {WORKFLOW_PATH}")
            logger.info("Please export your ComfyUI workflow in API format and save as fashion_tagger_api.json")
            return {}

        with open(WORKFLOW_PATH, 'r') as f:
            return json.load(f)

    def load_preferences(self) -> Dict:
        """Load designer preferences from file"""
        if not Path(PREFERENCE_FILE).exists():
            logger.warning(f"Preference file not found: {PREFERENCE_FILE}")
            return {"liked_tags": [], "disliked_tags": [], "liked_vectors": []}

        with open(PREFERENCE_FILE, 'r') as f:
            return json.load(f)

    def fetch_pending_images(self) -> List[Dict]:
        """Fetch pending images from server API"""
        try:
            response = requests.get(f"{SERVER_URL}/api/images/pending", timeout=30)
            response.raise_for_status()
            data = response.json()
            # API returns {"images": [...], "total": N, ...}
            return data.get("images", [])
        except Exception as e:
            logger.error(f"Failed to fetch pending images: {e}")
            return []

    def download_image(self, image_url: str, pin_id: str) -> Optional[Path]:
        """Download image to temp directory"""
        try:
            temp_path = TEMP_DIR / f"{pin_id}.jpg"
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            with open(temp_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Downloaded image: {pin_id}")
            return temp_path
        except Exception as e:
            logger.error(f"Failed to download image {pin_id}: {e}")
            return None

    def process_image_with_comfyui(self, image_path: Path) -> Optional[Dict]:
        """Send image to ComfyUI and get results"""
        if not self.workflow:
            logger.error("No workflow loaded, cannot process image")
            return None

        try:
            # Copy image to ComfyUI input directory
            import shutil
            comfyui_input_dir = Path.home() / "ComfyUI" / "input"
            comfyui_input_dir.mkdir(exist_ok=True)

            # Use just the filename for ComfyUI
            image_filename = image_path.name
            comfyui_image_path = comfyui_input_dir / image_filename
            shutil.copy(image_path, comfyui_image_path)
            logger.info(f"Copied image to ComfyUI input: {comfyui_image_path}")

            # Modify workflow to use the image filename (not full path)
            import copy
            workflow = copy.deepcopy(self.workflow)

            # Find LoadImage node and update with just the filename
            for node_id, node_data in workflow.items():
                if node_data.get("class_type") == "LoadImage":
                    node_data["inputs"]["image"] = image_filename
                    break

            # Queue the prompt
            prompt_id = self.comfy_client.queue_prompt(workflow)
            logger.info(f"Queued prompt: {prompt_id}")

            # Track progress
            history = self.comfy_client.track_progress(prompt_id)

            # Parse results from history
            results = self.parse_comfyui_results(history)
            return results

        except Exception as e:
            logger.error(f"Failed to process image with ComfyUI: {e}")
            return None

    def parse_comfyui_results(self, history: Dict) -> Dict:
        """Parse ComfyUI execution results"""
        results = {
            "tags_list": [],
            "fashion_tags": {},
            "ai_description": "",
            "aesthetic_score": 5.0,  # Default score
            "is_nsfw": False
        }

        try:
            # Extract outputs from history
            outputs = history.get("outputs", {})
            logger.info(f"Parsing outputs from nodes: {list(outputs.keys())}")

            for node_id, node_output in outputs.items():
                logger.info(f"Node {node_id} output keys: {list(node_output.keys())}")

                # WD14 Tagger output - tags is a list with one string of comma-separated tags
                if "tags" in node_output:
                    tags_data = node_output["tags"]
                    if isinstance(tags_data, list) and len(tags_data) > 0:
                        # Split the comma-separated string into individual tags
                        tags_str = tags_data[0]
                        results["tags_list"] = [t.strip() for t in tags_str.split(",")]
                        logger.info(f"Parsed {len(results['tags_list'])} tags")

                # PreviewAny output for Aesthetic Score (node 7) - text contains score as string
                if "text" in node_output and node_id == "7":
                    text_data = node_output["text"]
                    if isinstance(text_data, list) and len(text_data) > 0:
                        try:
                            score = float(text_data[0])
                            results["aesthetic_score"] = score
                            logger.info(f"Parsed aesthetic score: {score}")
                        except ValueError:
                            pass

                # PreviewAny output for Florence-2 caption (node 6)
                if "text" in node_output and node_id == "6":
                    text_data = node_output["text"]
                    if isinstance(text_data, list) and len(text_data) > 0:
                        results["ai_description"] = text_data[0]
                        logger.info(f"Parsed AI description: {text_data[0][:50]}...")

            # Categorize tags into fashion categories
            results["fashion_tags"] = self.categorize_tags(results["tags_list"])

            # Generate description from tags if no AI description
            if not results["ai_description"] and results["tags_list"]:
                results["ai_description"] = ", ".join(results["tags_list"][:20])

        except Exception as e:
            logger.error(f"Failed to parse ComfyUI results: {e}")

        return results

    def categorize_tags(self, tags: List[str]) -> Dict[str, List[str]]:
        """Categorize tags into fashion-specific categories"""
        categories = {
            "material": [],
            "style": [],
            "cut": [],
            "details": [],
            "color": []
        }

        # Material keywords
        materials = {'silk', 'cotton', 'linen', 'wool', 'leather', 'denim', 'velvet', 'satin', 'chiffon'}
        # Style keywords
        styles = {'minimalist', 'modern', 'vintage', 'bohemian', 'classic', 'casual', 'formal', 'streetwear'}
        # Cut keywords
        cuts = {'A-line', 'fitted', 'loose', 'oversized', 'slim', 'straight', 'flared'}
        # Detail keywords
        details = {'pleated', 'asymmetric', 'ruffled', 'embroidered', 'printed', 'striped', 'floral'}

        for tag in tags:
            tag_lower = tag.lower()
            if any(mat in tag_lower for mat in materials):
                categories["material"].append(tag)
            elif any(sty in tag_lower for sty in styles):
                categories["style"].append(tag)
            elif any(cut in tag_lower for cut in cuts):
                categories["cut"].append(tag)
            elif any(det in tag_lower for det in details):
                categories["details"].append(tag)

        return categories

    def calculate_tag_match_score(self, tags: List[str]) -> float:
        """Calculate how well tags match designer preferences"""
        if not self.preferences.get("liked_tags"):
            return 0.5  # Neutral score if no preferences

        liked_tags = set(self.preferences["liked_tags"])
        disliked_tags = set(self.preferences.get("disliked_tags", []))

        tag_set = set(tag.lower() for tag in tags)

        # Check for disliked tags (hard filter)
        if tag_set & disliked_tags:
            return 0.0

        # Calculate overlap with liked tags
        overlap = len(tag_set & liked_tags)
        if len(liked_tags) > 0:
            return min(overlap / len(liked_tags), 1.0)

        return 0.5

    def calculate_final_priority(self, results: Dict, image_vector: Optional[List[float]] = None) -> Tuple[float, int]:
        """
        Calculate final priority score using composite logic
        Returns: (priority_score, process_status)
        """
        tags = results.get("tags_list", [])
        aesthetic_score = results.get("aesthetic_score", 0.0)

        # Hard filter: Check blacklist tags
        tag_set = set(tag.lower() for tag in tags)
        if tag_set & BLACKLIST_TAGS:
            logger.info(f"Image filtered out due to blacklist tags: {tag_set & BLACKLIST_TAGS}")
            return 0.0, -1  # Mark as rejected

        # Calculate tag match score
        tag_match = self.calculate_tag_match_score(tags)

        # Calculate similarity score (placeholder - requires CLIP implementation)
        similarity = 0.5  # Default neutral
        if image_vector and self.preferences.get("liked_vectors"):
            # TODO: Implement CLIP vector similarity calculation
            # similarity = max(cosine_similarity(image_vector, liked_vec) for liked_vec in self.preferences["liked_vectors"])
            pass

        # Composite score: aesthetic * 0.4 + similarity * 0.4 + tag_match * 0.2
        final_score = (aesthetic_score / 10.0) * 0.4 + similarity * 0.4 + tag_match * 0.2

        # Determine process status
        if final_score >= 0.8:
            process_status = 2  # High priority - archive immediately
        elif final_score >= 0.5:
            process_status = 1  # Medium priority - needs review
        else:
            process_status = -1  # Low priority - reject

        logger.info(f"Priority calculation - Aesthetic: {aesthetic_score:.2f}, Tag Match: {tag_match:.2f}, "
                   f"Similarity: {similarity:.2f}, Final: {final_score:.2f}, Status: {process_status}")

        return final_score, process_status

    def send_results_to_server(self, pin_id: str, results: Dict, priority_score: float, process_status: int) -> bool:
        """Send processed results back to server"""
        try:
            # API only accepts these fields
            payload = {
                "pin_id": pin_id,
                "aesthetic_score": min(max(results.get("aesthetic_score", 5.0), 0.0), 10.0),  # Clamp to 0-10
                "fashion_tags": results.get("fashion_tags", {}),
                "description": results.get("ai_description", ""),
                "tags_list": results.get("tags_list", []),
                "is_nsfw": results.get("is_nsfw", False)
            }

            logger.info(f"Sending payload: aesthetic_score={payload['aesthetic_score']:.2f}, tags={len(payload['tags_list'])}")

            response = requests.post(f"{SERVER_URL}/api/tags/update", json=payload, timeout=30)
            response.raise_for_status()

            logger.info(f"Successfully sent results for {pin_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send results for {pin_id}: {e}")
            return False

    def cleanup_temp_image(self, image_path: Path):
        """Delete temporary image file"""
        try:
            if image_path.exists():
                image_path.unlink()
                logger.info(f"Cleaned up temp file: {image_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup {image_path}: {e}")

    def notify_high_priority(self, pin_id: str, score: float):
        """Send system notification for high-priority discoveries"""
        try:
            # macOS notification
            os.system(f'osascript -e \'display notification "Score: {score:.2f}" with title "FashionXG: High Priority Image Found" subtitle "Pin ID: {pin_id}"\'')
            logger.info(f"Sent notification for high-priority image: {pin_id}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def process_batch(self, batch_size: int = 10):
        """Process a batch of pending images"""
        logger.info(f"Fetching up to {batch_size} pending images...")
        pending_images = self.fetch_pending_images()

        if not pending_images:
            logger.info("No pending images to process")
            return 0

        # Limit batch size
        pending_images = pending_images[:batch_size]
        logger.info(f"Processing {len(pending_images)} images")

        processed_count = 0

        for image_data in pending_images:
            pin_id = image_data.get("pin_id")
            image_url = image_data.get("image_url")

            if not pin_id or not image_url:
                logger.warning(f"Skipping image with missing data: {image_data}")
                continue

            logger.info(f"Processing image: {pin_id}")

            # Download image
            image_path = self.download_image(image_url, pin_id)
            if not image_path:
                continue

            # Process with ComfyUI
            results = self.process_image_with_comfyui(image_path)
            if not results:
                self.cleanup_temp_image(image_path)
                continue

            # Calculate priority
            priority_score, process_status = self.calculate_final_priority(results)

            # Send results to server
            success = self.send_results_to_server(pin_id, results, priority_score, process_status)

            # Notify if high priority
            if priority_score >= 0.8:
                self.notify_high_priority(pin_id, priority_score)

            # Cleanup
            self.cleanup_temp_image(image_path)

            if success:
                processed_count += 1

            # Small delay between images
            time.sleep(1)

        logger.info(f"Batch complete: {processed_count}/{len(pending_images)} images processed successfully")
        return processed_count

    def run_continuous(self, batch_size: int = 10, sleep_minutes: int = 5):
        """Run bridge in continuous mode"""
        logger.info("Starting FashionXG Bridge in continuous mode")
        logger.info(f"Batch size: {batch_size}, Sleep interval: {sleep_minutes} minutes")

        while True:
            try:
                processed = self.process_batch(batch_size)

                if processed == 0:
                    logger.info(f"No images processed, sleeping for {sleep_minutes} minutes...")
                else:
                    logger.info(f"Processed {processed} images, sleeping for {sleep_minutes} minutes...")

                time.sleep(sleep_minutes * 60)

            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                logger.info("Sleeping for 1 minute before retry...")
                time.sleep(60)


def main():
    """Main entry point"""
    import argparse
    global SERVER_URL

    parser = argparse.ArgumentParser(description="FashionXG ComfyUI Bridge")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of images to process per batch")
    parser.add_argument("--sleep", type=int, default=5, help="Sleep interval in minutes between batches")
    parser.add_argument("--once", action="store_true", help="Process one batch and exit")
    parser.add_argument("--server", type=str, default=SERVER_URL, help="Server URL")

    args = parser.parse_args()

    # Update global config
    SERVER_URL = args.server

    # Create bridge instance
    bridge = FashionXGBridge()

    if args.once:
        logger.info("Running in single-batch mode")
        bridge.process_batch(args.batch_size)
    else:
        bridge.run_continuous(args.batch_size, args.sleep)


if __name__ == "__main__":
    main()

