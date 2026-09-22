# BorderEye AI — Face recognizer (ArcFace cosine matching)
#
# The stored watchlist embeddings are L2-normalized; matching is pure cosine
# similarity against every stored embedding, keeping the best hit.
import numpy as np

from .watchlist_manager import WatchlistManager

DEFAULT_THRESHOLD = 0.45  # buffalo_l ArcFace; lower = more permissive


class FaceRecognizer:
    def __init__(self, manager: WatchlistManager, threshold: float = DEFAULT_THRESHOLD) -> None:
        self.manager = manager
        self.threshold = threshold

    def identify(self, embedding: np.ndarray) -> dict:
        """Map a face embedding to a recognition verdict.

        Returns per-object identity fields including status and designation
        required by face_pipeline.py:
          {"label", "watchlist", "confidence", "status", "designation"}
        """
        person, sim = self.manager.best_match(embedding, threshold=self.threshold)
        if person is None:
            return {
                "label": "Unknown",
                "watchlist": False,
                "confidence": round(max(sim, 0.0), 3),
                "status": "INTRUDER",
                "designation": "Unauthorized Entity",
            }
        return {
            "label": person["name"],
            "watchlist": True,
            "confidence": round(sim, 3),
            "status": "AUTHORIZED",
            "designation": person.get("designation", "Authorized Personnel"),
        }
