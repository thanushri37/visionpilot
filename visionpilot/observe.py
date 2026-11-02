"""VisionPilot's eyes: look at the page and number everything clickable.

observe(page, run_dir, n) does three things:
  1. finds every visible link, button, text box and dropdown
  2. saves a plain screenshot (for the checker) and a numbered one (for the model)
  3. returns a list like  [5] button "Save settings"
The model answers with a number; the code uses that number to find the
real element, so the model never has to guess pixel positions.
"""
import io
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Everything VisionPilot might click or type into.
SELECTOR = "a, button, input, select, textarea, [role=button]"


@dataclass
class Observation:
    raw_path: str          # plain screenshot, for the checker
    labeled_path: str      # screenshot with numbered red boxes, for the model
    url: str
    elements: list = field(default_factory=list)   # what each number means
    handles: list = field(default_factory=list)    # the real elements, same order

    def element_lines(self):
        """The text list sent to the model with the picture."""
        lines = []
        for e in self.elements:
            kind = e["tag"] + (f"({e['type']})" if e["type"] else "")
            line = f'[{e["id"]}] {kind} "{e["text"]}"'
            if e["value"]:
                line += f' value="{e["value"]}"'
            lines.append(line)
        return "\n".join(lines)


def _name(handle):
    """The best human-readable name for an element."""
    for attr in ("aria-label", "placeholder"):
        value = handle.get_attribute(attr)
        if value:
            return value
    text = handle.inner_text()
    return text or handle.get_attribute("name") or ""


def _font():
    try:
        return ImageFont.load_default(size=14)   # Pillow 10.1 and newer
    except TypeError:
        return ImageFont.load_default()


def observe(page, run_dir, n):
    """Look at the page now. n is the step number, used in file names."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    obs = Observation(
        raw_path=str(run_dir / f"step-{n:02d}-raw.png"),
        labeled_path=str(run_dir / f"step-{n:02d}-labeled.png"),
        url=page.url,
    )

    # 1. Find every visible interactive element, in page order.
    for handle in page.query_selector_all(SELECTOR):
        box = handle.bounding_box()
        if not handle.is_visible() or not box or box["width"] < 2 or box["height"] < 2:
            continue
        tag = handle.evaluate("e => e.tagName.toLowerCase()")
        value = handle.input_value() if tag in ("input", "select", "textarea") else ""
        obs.elements.append({
            "id": len(obs.elements) + 1,
            "tag": tag,
            "type": handle.get_attribute("type") or "",
            "text": " ".join(_name(handle).split())[:60],
            "value": value,
            "box": box,
        })
        obs.handles.append(handle)

    # 2. Plain screenshot, then a copy with a numbered red box on each element.
    png = page.screenshot(path=obs.raw_path)
    img = Image.open(io.BytesIO(png)).convert("RGB")
    draw = ImageDraw.Draw(img)
    font = _font()
    for e in obs.elements:
        b = e["box"]
        x0, y0, x1, y1 = b["x"], b["y"], b["x"] + b["width"], b["y"] + b["height"]
        draw.rectangle([x0, y0, x1, y1], outline="red", width=2)
        label = str(e["id"])
        tag_w, tag_h = 10 + 9 * len(label), 18
        # Put the number tag where it won't cover the element's words:
        # above the box if there's room, otherwise to its left, otherwise below.
        if y0 >= tag_h:
            tx, ty = x0, y0 - tag_h
        elif x0 >= tag_w:
            tx, ty = x0 - tag_w, y0
        else:
            tx, ty = x0, y1
        draw.rectangle([tx, ty, tx + tag_w, ty + tag_h], fill="red")
        draw.text((tx + 4, ty + 1), label, fill="white", font=font)
    img.save(obs.labeled_path)
    return obs
