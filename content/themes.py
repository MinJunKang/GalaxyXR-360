"""53 themes x (2 photo scenes + 2 video scenes) = 106 photos + 106 videos.
photo : the full 360-degree surroundings for DiT360 (ahead, sides, behind, sky above, ground below, light, color, texture).
video : (front, motion, around)
  front  = what the static perspective camera sees (Wan2.2 clip, horizontal FOV 90, level with the horizon)
  motion = slow natural motion inside the scene (the camera never moves)
  around = the rest of the sphere, so CubeComposer completes the sides, back, sky and ground consistently
Theme data lives in themes_nature.py (healing, ocean, underwater) and themes_worlds.py (space, sci-fi, desert,
countryside, jurassic, medieval, fantasy, city)."""
T = []


def add(i, cat, ko, photos, videos):
    assert len(photos) == 2 and len(videos) == 2 and all(len(v) == 3 for v in videos), i
    T.append(dict(id=i, category=cat, ko=ko, photo=photos, video=videos))


import themes_nature  # noqa: E402,F401
import themes_worlds  # noqa: E402,F401

assert len(T) == 53, len(T)
assert len({t['id'] for t in T}) == 53
