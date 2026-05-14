import io
import os
import re
import uuid
from urllib.parse import quote

from dotenv import load_dotenv
import httpx
from huggingface_hub import InferenceClient
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from backend.openai_service import generate_architecture


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

GENERATED_DIR = os.path.join(ROOT_DIR, "frontend", "generated")
REFERENCE_DIR = os.path.join(ROOT_DIR, "frontend", "reference_library")
IMAGE_PROVIDER = (os.getenv("IMAGE_PROVIDER") or "flux").strip().lower()
HF_TOKEN = (os.getenv("HF_TOKEN") or "").strip()
HF_PROVIDER = (os.getenv("HF_PROVIDER") or "hf-inference").strip()
HF_IMAGE_MODEL = (
    os.getenv("HF_IMAGE_MODEL") or "black-forest-labs/FLUX.1-schnell"
).strip()
SERPAPI_API_KEY = (os.getenv("SERPAPI_API_KEY") or "").strip()
FLUX_WIDTH = int((os.getenv("FLUX_WIDTH") or "1024").strip())
FLUX_HEIGHT = int((os.getenv("FLUX_HEIGHT") or "768").strip())
FLUX_STEPS = int((os.getenv("FLUX_STEPS") or "4").strip())
FLUX_GUIDANCE_SCALE = float((os.getenv("FLUX_GUIDANCE_SCALE") or "3.5").strip())
PRO_CARD_WIDTH = int((os.getenv("PRO_CARD_WIDTH") or "1600").strip())
PRO_CARD_HEIGHT = int((os.getenv("PRO_CARD_HEIGHT") or "900").strip())

LOCAL_REFERENCE_MAP = {
    "ai": ["ai_reference.png"],
    "ml": ["ml_reference.png"],
    "ds": ["ds_reference.png"],
    "nlp": ["nlp_reference.png"],
    "dl": ["dl_reference.png"],
    "neural_network": ["neural_network_reference.png"],
    "cnn": ["cnn_reference.webp", "working_of_cnn__.webp"],
    "rnn": ["rnn_reference.webp", "introduction_to_recurrent_neural_network.webp"],
    "lstm": ["lstm_reference.webp", "Long-Short-Term-Memory-LSTM-neural-network-model-diagram-The-LSTM-consists-of-three.webp"],
}


def _ensure_output_dir():
    os.makedirs(GENERATED_DIR, exist_ok=True)


def _ensure_reference_dir():
    os.makedirs(REFERENCE_DIR, exist_ok=True)


def _save_image(image: Image.Image):
    _ensure_output_dir()
    filename = f"generated-image-{uuid.uuid4().hex}.png"
    output_path = os.path.join(GENERATED_DIR, filename)
    image.save(output_path, format="PNG")
    return f"/generated/{filename}"


def _save_downloaded_image(raw_bytes, prefix="reference-image"):
    _ensure_output_dir()
    image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    filename = f"{prefix}-{uuid.uuid4().hex}.png"
    output_path = os.path.join(GENERATED_DIR, filename)
    image.save(output_path, format="PNG")
    return f"/generated/{filename}"


def _load_font(size, bold=False):
    candidates = []
    if os.name == "nt":
        windows_fonts = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
        candidates.extend([
            os.path.join(windows_fonts, "seguiemj.ttf"),
            os.path.join(windows_fonts, "segoeuib.ttf" if bold else "segoeui.ttf"),
            os.path.join(windows_fonts, "arialbd.ttf" if bold else "arial.ttf"),
        ])

    for path in candidates:
        if path and os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue

    return ImageFont.load_default()


def _fit_and_crop(image, size):
    target_width, target_height = size
    src_width, src_height = image.size
    scale = max(target_width / src_width, target_height / src_height)
    resized = image.resize(
        (int(src_width * scale), int(src_height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = max((resized.width - target_width) // 2, 0)
    top = max((resized.height - target_height) // 2, 0)
    return resized.crop((left, top, left + target_width, top + target_height))


def _wrap_text(draw, text, font, max_width):
    words = (text or "").split()
    if not words:
        return []

    lines = []
    current = words[0]
    for word in words[1:]:
        test_line = f"{current} {word}"
        if draw.textlength(test_line, font=font) <= max_width:
            current = test_line
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _compose_professional_card(image, prompt, overlay_content=None):
    card = Image.new("RGB", (PRO_CARD_WIDTH, PRO_CARD_HEIGHT), "#09111f")
    draw = ImageDraw.Draw(card)

    left_panel_width = int(PRO_CARD_WIDTH * 0.68)
    right_panel_x = left_panel_width + 28
    right_panel_width = PRO_CARD_WIDTH - right_panel_x - 36

    visual = _fit_and_crop(image.convert("RGB"), (left_panel_width, PRO_CARD_HEIGHT))
    card.paste(visual, (0, 0))

    # Add a border and divider so the layout looks more like a presentation slide.
    draw.rounded_rectangle(
        [(18, 18), (left_panel_width - 18, PRO_CARD_HEIGHT - 18)],
        radius=24,
        outline="#16385c",
        width=4,
    )
    draw.rectangle(
        [(left_panel_width, 0), (PRO_CARD_WIDTH, PRO_CARD_HEIGHT)],
        fill="#0d1728",
    )
    draw.line(
        [(left_panel_width, 36), (left_panel_width, PRO_CARD_HEIGHT - 36)],
        fill="#21486f",
        width=3,
    )

    title_font = _load_font(42, bold=True)
    section_font = _load_font(20, bold=True)
    body_font = _load_font(22, bold=False)
    small_font = _load_font(18, bold=False)

    title = (overlay_content or {}).get("title") or "AI Concept Visual"
    bullets = list((overlay_content or {}).get("bullets") or [])

    prompt_summary = prompt.strip()
    if len(prompt_summary) > 140:
        prompt_summary = prompt_summary[:137].rstrip() + "..."

    y = 48
    draw.text((right_panel_x, y), "AI VISUAL", font=small_font, fill="#58c7ff")
    y += 34

    for line in _wrap_text(draw, title, title_font, right_panel_width):
        draw.text((right_panel_x, y), line, font=title_font, fill="#f3f7ff")
        y += 50

    y += 8
    draw.text((right_panel_x, y), "English Summary", font=section_font, fill="#9fdcff")
    y += 34

    for line in _wrap_text(draw, prompt_summary, body_font, right_panel_width):
        draw.text((right_panel_x, y), line, font=body_font, fill="#d8e6ff")
        y += 32

    y += 18
    draw.text((right_panel_x, y), "Key Points", font=section_font, fill="#9fdcff")
    y += 34

    for bullet in bullets[:4]:
        bullet_lines = _wrap_text(draw, bullet, body_font, right_panel_width - 26)
        if not bullet_lines:
            continue
        draw.ellipse(
            [(right_panel_x, y + 10), (right_panel_x + 10, y + 20)],
            fill="#58c7ff",
        )
        draw.text((right_panel_x + 22, y), bullet_lines[0], font=body_font, fill="#f3f7ff")
        y += 32
        for extra_line in bullet_lines[1:]:
            draw.text((right_panel_x + 22, y), extra_line, font=body_font, fill="#c4d8f3")
            y += 30
        y += 12
        if y > PRO_CARD_HEIGHT - 80:
            break

    footer = "Professional English educational layout"
    draw.text((right_panel_x, PRO_CARD_HEIGHT - 42), footer, font=small_font, fill="#6fa4d0")
    return card


def _guided_stage_titles(topic_family):
    stage_map = {
        "cnn": [
            "Input Tensor", "Convolution", "ReLU", "Pooling",
            "Feature Maps", "Flatten", "Dense", "Softmax"
        ],
        "bpnn": [
            "Input Features", "Hidden Layer 1", "Hidden Layer 2",
            "Output Layer", "Loss", "Backpropagation", "Weight Update"
        ],
        "neural_network": [
            "Input Layer", "Hidden Layer 1", "Hidden Layer 2", "Output Layer"
        ],
        "transformer": [
            "Tokens", "Embeddings", "Positional Encoding", "Q/K/V",
            "Multi-Head Attention", "Add + Norm", "Feed Forward", "Output Logits"
        ],
        "rnn": [
            "Input t1", "Hidden State h1", "Input t2", "Hidden State h2",
            "Input t3", "Hidden State h3", "Sequence Output"
        ],
        "lstm": [
            "Input x_t", "Forget Gate", "Input Gate", "Cell State",
            "Output Gate", "Hidden State h_t"
        ],
        "rag": [
            "User Query", "Embedding", "Vector Search", "Top-k Retrieval",
            "Prompt Assembly", "LLM Generation", "Grounded Answer"
        ],
        "bert": [
            "Tokenize", "Embeddings", "Encoder Block 1", "Encoder Block 2",
            "Contextual Vectors", "Task Head"
        ],
        "gpt": [
            "Prompt Tokens", "Embeddings", "Masked Attention", "Decoder Block",
            "Next-Token Logits", "Autoregressive Output"
        ],
        "nlp": [
            "Input Text", "Tokenize", "Embeddings", "Language Model", "Task Output"
        ],
        "dl": [
            "Input Data", "Feature Extractor", "Hidden Representation", "Loss",
            "Optimizer", "Prediction"
        ],
        "ds": [
            "Collect Data", "Clean Data", "EDA", "Feature Engineering", "Model", "Insights"
        ],
        "ml": [
            "Dataset", "Split Data", "Preprocess", "Train Model", "Evaluate", "Predict"
        ],
        "ai": [
            "Input Data", "Representation", "Learning", "Inference", "Decision"
        ],
    }
    return stage_map.get(topic_family, stage_map["ai"])


def _prepare_guided_background(image, size):
    visual = _fit_and_crop(image.convert("RGB"), size)
    softened = visual.filter(ImageFilter.GaussianBlur(radius=4))
    tint = Image.new("RGB", size, "#102341")
    return Image.blend(softened, tint, 0.38)


def _compose_guided_flux_card(image, prompt, overlay_content=None):
    card = Image.new("RGB", (PRO_CARD_WIDTH, PRO_CARD_HEIGHT), "#09111f")
    draw = ImageDraw.Draw(card)

    left_panel_width = int(PRO_CARD_WIDTH * 0.68)
    right_panel_x = left_panel_width + 28
    right_panel_width = PRO_CARD_WIDTH - right_panel_x - 36

    visual = _prepare_guided_background(image, (left_panel_width, PRO_CARD_HEIGHT))
    card.paste(visual, (0, 0))

    draw.rounded_rectangle(
        [(18, 18), (left_panel_width - 18, PRO_CARD_HEIGHT - 18)],
        radius=24,
        outline="#16385c",
        width=4,
    )
    draw.rectangle(
        [(left_panel_width, 0), (PRO_CARD_WIDTH, PRO_CARD_HEIGHT)],
        fill="#0d1728",
    )
    draw.line(
        [(left_panel_width, 36), (left_panel_width, PRO_CARD_HEIGHT - 36)],
        fill="#21486f",
        width=3,
    )

    title_font = _load_font(42, bold=True)
    section_font = _load_font(20, bold=True)
    body_font = _load_font(22, bold=False)
    small_font = _load_font(18, bold=False)
    stage_font = _load_font(19, bold=True)

    title = (overlay_content or {}).get("title") or "AI Concept Visual"
    bullets = list((overlay_content or {}).get("bullets") or [])
    prompt_summary = prompt.strip()
    if len(prompt_summary) > 140:
        prompt_summary = prompt_summary[:137].rstrip() + "..."

    topic_family = _detect_topic_family(prompt)
    stage_titles = _guided_stage_titles(topic_family)

    draw.text((30, 34), "ENGLISH AI VISUAL", font=small_font, fill="#92ecff")
    title_box = (30, 68, left_panel_width - 36, 170)
    _draw_wrapped_text(draw, title, title_font, "#f4f8ff", title_box, line_spacing=6)

    diagram_box = (40, 210, left_panel_width - 40, PRO_CARD_HEIGHT - 54)
    draw.rounded_rectangle(
        diagram_box,
        radius=28,
        fill="#0b1730",
        outline="#2a628f",
        width=2,
    )

    box_width = 145
    box_height = 74
    usable_width = (diagram_box[2] - diagram_box[0]) - 120
    usable_height = (diagram_box[3] - diagram_box[1]) - 120
    stage_count = len(stage_titles)
    columns = min(stage_count, 4)
    rows = 2 if stage_count > 4 else 1
    x_gap = usable_width / max(columns - 1, 1)
    y_gap = usable_height / max(rows - 1, 1) if rows > 1 else 0

    box_positions = []
    for index, stage_title in enumerate(stage_titles):
        row = index // columns
        col = index % columns
        x_center = diagram_box[0] + 60 + col * x_gap
        y_center = diagram_box[1] + 90 + row * y_gap
        if rows == 1:
            y_center = (diagram_box[1] + diagram_box[3]) / 2
        box = (
            int(x_center - box_width / 2),
            int(y_center - box_height / 2),
            int(x_center + box_width / 2),
            int(y_center + box_height / 2),
        )
        box_positions.append(box)
        fill = "#12385f" if (index % 2 == 0) else "#18507a"
        outline = "#73e6ff"
        _draw_labeled_box(draw, box, stage_title, stage_font, fill, outline, "#eff8ff")

    for index in range(len(box_positions) - 1):
        current = box_positions[index]
        nxt = box_positions[index + 1]
        same_row = abs(((current[1] + current[3]) // 2) - ((nxt[1] + nxt[3]) // 2)) < 30
        if same_row:
            start = (current[2], (current[1] + current[3]) // 2)
            end = (nxt[0], (nxt[1] + nxt[3]) // 2)
        else:
            start = ((current[0] + current[2]) // 2, current[3])
            end = ((nxt[0] + nxt[2]) // 2, nxt[1])
        _draw_arrow(draw, start, end, fill="#7ae7ff", width=4, arrow_size=12)

    y = 48
    draw.text((right_panel_x, y), "AI VISUAL", font=small_font, fill="#58c7ff")
    y += 34

    for line in _wrap_text(draw, title, title_font, right_panel_width):
        draw.text((right_panel_x, y), line, font=title_font, fill="#f3f7ff")
        y += 50

    y += 8
    draw.text((right_panel_x, y), "English Summary", font=section_font, fill="#9fdcff")
    y += 34

    for line in _wrap_text(draw, prompt_summary, body_font, right_panel_width):
        draw.text((right_panel_x, y), line, font=body_font, fill="#d8e6ff")
        y += 32

    y += 18
    draw.text((right_panel_x, y), "Key Points", font=section_font, fill="#9fdcff")
    y += 34

    for bullet in bullets[:4]:
        bullet_lines = _wrap_text(draw, bullet, body_font, right_panel_width - 26)
        if not bullet_lines:
            continue
        draw.ellipse(
            [(right_panel_x, y + 10), (right_panel_x + 10, y + 20)],
            fill="#58c7ff",
        )
        draw.text((right_panel_x + 22, y), bullet_lines[0], font=body_font, fill="#f3f7ff")
        y += 32
        for extra_line in bullet_lines[1:]:
            draw.text((right_panel_x + 22, y), extra_line, font=body_font, fill="#c4d8f3")
            y += 30
        y += 12
        if y > PRO_CARD_HEIGHT - 80:
            break

    footer = "Programmatic English labels over Flux visual background"
    draw.text((right_panel_x, PRO_CARD_HEIGHT - 42), footer, font=small_font, fill="#6fa4d0")
    return card


def _parse_mermaid_nodes_and_edges(mermaid_text):
    node_map = {}
    edges = []
    pattern = re.compile(r'([A-Za-z0-9_]+)\[(.*?)\]\s*-->\s*([A-Za-z0-9_]+)\[(.*?)\]')
    for line in (mermaid_text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("flowchart"):
            continue
        match = pattern.search(line)
        if not match:
            continue
        source_id, source_label, target_id, target_label = match.groups()
        node_map[source_id] = source_label.strip()
        node_map[target_id] = target_label.strip()
        edges.append((source_id, target_id))
    return node_map, edges


def _layout_layers(node_ids, edges):
    indegree = {node_id: 0 for node_id in node_ids}
    children = {node_id: [] for node_id in node_ids}
    for source_id, target_id in edges:
        if source_id in indegree and target_id in indegree:
            indegree[target_id] += 1
            children[source_id].append(target_id)

    layers = {}
    queue = [node_id for node_id, degree in indegree.items() if degree == 0]
    if not queue:
        queue = list(node_ids)

    for node_id in queue:
        layers[node_id] = 0

    queue_index = 0
    while queue_index < len(queue):
        node_id = queue[queue_index]
        queue_index += 1
        for child_id in children.get(node_id, []):
            candidate_depth = layers[node_id] + 1
            current_depth = layers.get(child_id, -1)
            if candidate_depth > current_depth:
                layers[child_id] = candidate_depth
            queue.append(child_id)

    for node_id in node_ids:
        layers.setdefault(node_id, 0)

    grouped = {}
    for node_id, depth in layers.items():
        grouped.setdefault(depth, []).append(node_id)

    return [grouped[index] for index in sorted(grouped)]


def _draw_wrapped_text(draw, text, font, fill, box, line_spacing=8):
    x0, y0, x1, y1 = box
    lines = _wrap_text(draw, text, font, x1 - x0)
    y = y0
    for line in lines:
        draw.text((x0, y), line, font=font, fill=fill)
        y += font.size + line_spacing
        if y > y1:
            break


def _draw_arrow(draw, start, end, fill, width=4, arrow_size=12, dashed=False):
    if dashed:
        segments = 12
        for index in range(segments):
            if index % 2 == 1:
                continue
            t0 = index / segments
            t1 = min((index + 1) / segments, 1)
            sx = start[0] + (end[0] - start[0]) * t0
            sy = start[1] + (end[1] - start[1]) * t0
            ex = start[0] + (end[0] - start[0]) * t1
            ey = start[1] + (end[1] - start[1]) * t1
            draw.line([(sx, sy), (ex, ey)], fill=fill, width=width)
    else:
        draw.line([start, end], fill=fill, width=width)

    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux = dx / length
    uy = dy / length
    left = (end[0] - ux * arrow_size - uy * arrow_size * 0.55, end[1] - uy * arrow_size + ux * arrow_size * 0.55)
    right = (end[0] - ux * arrow_size + uy * arrow_size * 0.55, end[1] - uy * arrow_size - ux * arrow_size * 0.55)
    draw.polygon([end, left, right], fill=fill)


def _draw_centered_text(draw, center, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    draw.text((center[0] - width / 2, center[1] - height / 2), text, font=font, fill=fill)


def _draw_labeled_box(draw, box, text, font, fill, outline, text_fill):
    draw.rounded_rectangle(box, radius=20, fill=fill, outline=outline, width=3)
    _draw_wrapped_text(draw, text, font, text_fill, (box[0] + 14, box[1] + 14, box[2] - 14, box[3] - 14), line_spacing=4)


def _draw_summary_panel(draw, right_x0, right_x1, title, explanation, overlay_content=None, footer_text="Topic-accurate AI diagram"):
    title_font = _load_font(40, bold=True)
    section_font = _load_font(22, bold=True)
    body_font = _load_font(21, bold=False)
    small_font = _load_font(18, bold=False)

    draw.text((right_x0, 46), "AI VISUAL", font=small_font, fill="#57c4ff")
    _draw_wrapped_text(draw, title, title_font, "#f5f8ff", (right_x0, 80, right_x1, 180))
    draw.text((right_x0, 210), "English Summary", font=section_font, fill="#9fdcff")
    _draw_wrapped_text(draw, explanation, body_font, "#d8e6ff", (right_x0, 248, right_x1, 405))
    draw.text((right_x0, 435), "Key Points", font=section_font, fill="#9fdcff")

    bullet_y = 475
    bullets = list((overlay_content or {}).get("bullets") or [])
    for bullet in bullets[:4]:
        wrapped_lines = _wrap_text(draw, bullet, body_font, (right_x1 - right_x0) - 24)
        if not wrapped_lines:
            continue
        draw.ellipse([(right_x0, bullet_y + 10), (right_x0 + 10, bullet_y + 20)], fill="#57c4ff")
        draw.text((right_x0 + 22, bullet_y), wrapped_lines[0], font=body_font, fill="#f3f7ff")
        bullet_y += 32
        for extra_line in wrapped_lines[1:]:
            draw.text((right_x0 + 22, bullet_y), extra_line, font=body_font, fill="#c4d8f3")
            bullet_y += 30
        bullet_y += 12
        if bullet_y > PRO_CARD_HEIGHT - 120:
            break

    draw.text((right_x0, PRO_CARD_HEIGHT - 46), footer_text, font=small_font, fill="#6fa4d0")


def _create_two_panel_canvas(title, explanation):
    canvas = Image.new("RGB", (PRO_CARD_WIDTH, PRO_CARD_HEIGHT), "#08111f")
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [(22, 22), (PRO_CARD_WIDTH - 22, PRO_CARD_HEIGHT - 22)],
        radius=28,
        outline="#173756",
        width=3,
    )
    left_x0 = 48
    left_x1 = int(PRO_CARD_WIDTH * 0.71)
    right_x0 = left_x1 + 34
    right_x1 = PRO_CARD_WIDTH - 44
    diagram_box = (left_x0, 70, left_x1, PRO_CARD_HEIGHT - 78)
    return canvas, draw, diagram_box, right_x0, right_x1


def _render_cnn_architecture_diagram(title, explanation, overlay_content=None):
    canvas, draw, diagram_box, right_x0, right_x1 = _create_two_panel_canvas(title, explanation)
    left_x0, top, left_x1, bottom = diagram_box
    draw.rounded_rectangle(diagram_box, radius=26, fill="#f7f7f3", outline="#d2d8e1", width=2)

    title_font = _load_font(22, bold=True)
    label_font = _load_font(18, bold=True)
    small_font = _load_font(16, bold=False)
    draw.text((left_x0 + 24, top + 18), "Convolutional Neural Network (CNN)", font=title_font, fill="#21304d")

    input_box = (left_x0 + 25, top + 180, left_x0 + 95, top + 250)
    draw.rectangle(input_box, fill="#e8ebef", outline="#b7bfcc", width=2)
    draw.text((input_box[0] + 10, input_box[3] + 8), "Input", font=label_font, fill="#20283a")
    draw.text((input_box[0] + 2, input_box[3] + 34), "Image", font=label_font, fill="#20283a")

    group_xs = [left_x0 + 145, left_x0 + 310, left_x0 + 475, left_x0 + 640]
    group_y = top + 128
    for index, group_x in enumerate(group_xs):
        for depth in range(8):
            offset = depth * 7
            draw.rectangle(
                (group_x + offset, group_y + offset, group_x + 70 + offset, group_y + 120 + offset),
                outline="#2f9851",
                fill="#dff4e3" if depth < 7 else "#2f9851",
                width=2,
            )
        block_center_x = group_x + 62
        draw.text((group_x - 2, top + 88), "Pooling", font=small_font, fill="#28354b")
        draw.text((group_x - 12, group_y + 150), "Convolution +", font=small_font, fill="#28354b")
        draw.text((group_x + 24, group_y + 174), "ReLU", font=small_font, fill="#28354b")
        if index < len(group_xs) - 1:
            _draw_arrow(draw, (block_center_x + 58, group_y + 78), (group_xs[index + 1] - 24, group_y + 78), fill="#333333", width=2, arrow_size=8)

    draw.line((group_xs[0] - 18, top + 66, group_xs[-1] + 95, top + 66), fill="#1f1f1f", width=2)
    _draw_arrow(draw, (group_xs[0] - 18, top + 66), (group_xs[0] - 4, top + 66), fill="#1f1f1f", width=2, arrow_size=8)
    _draw_arrow(draw, (group_xs[-1] + 95, top + 66), (group_xs[-1] + 80, top + 66), fill="#1f1f1f", width=2, arrow_size=8)
    draw.text((group_xs[1] + 28, top + 34), "Feature Maps", font=label_font, fill="#111111")

    flatten_x = group_xs[-1] + 130
    draw.rectangle((flatten_x, top + 135, flatten_x + 24, top + 355), fill="#ffeec2", outline="#f2d98b", width=1)
    draw.text((flatten_x + 2, top + 214), "Flattened", font=small_font, fill="#20283a", anchor="mm")

    fc_center_x = flatten_x + 125
    input_nodes = [(fc_center_x - 40, top + 130 + i * 55) for i in range(6)]
    output_nodes = [(fc_center_x + 70, top + 165 + i * 65) for i in range(4)]
    for start in input_nodes:
        for end in output_nodes:
            draw.line((start[0], start[1], end[0], end[1]), fill="#222222", width=1)
    for center in input_nodes:
        draw.ellipse((center[0] - 14, center[1] - 14, center[0] + 14, center[1] + 14), fill="#d9e5ff", outline="#adc2ef", width=2)
    scores = ["0.30", "0.10", "0.20", "0.90"]
    for index, center in enumerate(output_nodes):
        draw.ellipse((center[0] - 14, center[1] - 14, center[0] + 14, center[1] + 14), fill="#ffd5db", outline="#ffb2bd", width=2)
        draw.text((center[0] + 30, center[1] - 10), scores[index], font=small_font, fill="#111111")

    draw.line((fc_center_x - 42, top + 92, fc_center_x + 70, top + 92), fill="#2a2a2a", width=2)
    draw.line((fc_center_x - 42, top + 92, fc_center_x - 42, top + 102), fill="#2a2a2a", width=2)
    draw.line((fc_center_x + 70, top + 92, fc_center_x + 70, top + 102), fill="#2a2a2a", width=2)
    draw.text((fc_center_x - 34, top + 48), "Fully Connected Layer", font=label_font, fill="#111111")

    draw.line((left_x0 + 8, bottom - 55, flatten_x - 10, bottom - 55), fill="#707784", width=2)
    draw.line((left_x0 + 8, bottom - 55, left_x0 + 8, bottom - 80), fill="#707784", width=2)
    draw.line((flatten_x - 10, bottom - 55, flatten_x - 10, bottom - 80), fill="#707784", width=2)
    draw.text((left_x0 + 260, bottom - 40), "Feature Extraction", font=label_font, fill="#1e2638")

    draw.line((flatten_x + 15, bottom - 55, left_x1 - 10, bottom - 55), fill="#707784", width=2)
    draw.line((flatten_x + 15, bottom - 55, flatten_x + 15, bottom - 80), fill="#707784", width=2)
    draw.line((left_x1 - 10, bottom - 55, left_x1 - 10, bottom - 80), fill="#707784", width=2)
    draw.text((flatten_x + 60, bottom - 40), "Classification", font=label_font, fill="#1e2638")

    _draw_summary_panel(draw, right_x0, right_x1, title, explanation, overlay_content, footer_text="Deterministic CNN architecture diagram")
    return canvas


def _render_rnn_unrolled_diagram(title, explanation, overlay_content=None):
    canvas, draw, diagram_box, right_x0, right_x1 = _create_two_panel_canvas(title, explanation)
    left_x0, top, left_x1, bottom = diagram_box
    draw.rounded_rectangle(diagram_box, radius=26, fill="#fafaf7", outline="#d8dde6", width=2)

    title_font = _load_font(22, bold=True)
    label_font = _load_font(18, bold=True)
    small_font = _load_font(16, bold=False)
    draw.text((left_x0 + 130, top + 18), "Working of Recurrent Neural Network", font=title_font, fill="#1f2435")

    time_xs = [left_x0 + 160, left_x0 + 360, left_x0 + 560, left_x0 + 760]
    y_h = top + 250
    y_x = top + 360
    y_l = top + 150

    for i, x in enumerate(time_xs):
        h_box = (x - 52, y_h - 28, x + 52, y_h + 28)
        draw.rectangle(h_box, fill="#e2f1db", outline="#80948a", width=2)
        h_label = "h" if i == 0 else f"h_t{'+' + str(i-1) if i > 1 else ''}".replace("+0", "")
        if i == 1:
            h_label = "h_t-1"
        elif i == 2:
            h_label = "h_t"
        elif i == 3:
            h_label = "h_t+1"
        draw.text((x - 16, y_h - 12), h_label, font=label_font, fill="#182233")

        draw.ellipse((x - 34, y_x - 34, x + 34, y_x + 34), fill="#10a372", outline="#0b6d50", width=2)
        x_label = "X" if i == 0 else f"X_t{'+' + str(i-1) if i > 1 else ''}".replace("+0", "")
        if i == 1:
            x_label = "X_t-1"
        elif i == 2:
            x_label = "X_t"
        elif i == 3:
            x_label = "X_t+1"
        draw.text((x - 18, y_x - 12), x_label, font=label_font, fill="#f7fffb")

        draw.ellipse((x - 34, y_l - 34, x + 34, y_l + 34), fill="#6fbce5", outline="#4e90b8", width=2)
        l_label = "L" if i == 0 else f"L_t{'+' + str(i-1) if i > 1 else ''}".replace("+0", "")
        if i == 1:
            l_label = "L_t-1"
        elif i == 2:
            l_label = "L_t"
        elif i == 3:
            l_label = "L_t+1"
        draw.text((x - 18, y_l - 12), l_label, font=label_font, fill="#f5fbff")

        _draw_arrow(draw, (x, y_x - 34), (x, y_h + 28), fill="#222222", width=2, arrow_size=8)
        _draw_arrow(draw, (x, y_h - 28), (x, y_l + 34), fill="#222222", width=2, arrow_size=8)
        draw.text((x + 18, y_h + 52), "u", font=small_font, fill="#111111")
        draw.text((x + 18, y_h - 52), "w", font=small_font, fill="#111111")
        if i < len(time_xs) - 1:
            _draw_arrow(draw, (x + 52, y_h), (time_xs[i + 1] - 52, y_h), fill="#222222", width=3, arrow_size=10)
            draw.text((x + 92, y_h - 28), "v", font=small_font, fill="#111111")

    draw.text((left_x0 + 18, y_h - 16), "Unfold", font=label_font, fill="#111111")
    draw.text((left_x0 + 265, y_h + 85), "Time-unrolled hidden state transitions", font=small_font, fill="#334155")

    _draw_summary_panel(draw, right_x0, right_x1, title, explanation, overlay_content, footer_text="Deterministic RNN unrolled diagram")
    return canvas


def _render_lstm_cell_diagram(title, explanation, overlay_content=None):
    canvas, draw, diagram_box, right_x0, right_x1 = _create_two_panel_canvas(title, explanation)
    left_x0, top, left_x1, bottom = diagram_box
    draw.rounded_rectangle(diagram_box, radius=26, fill="#fbfbf8", outline="#d8dde6", width=2)

    title_font = _load_font(22, bold=True)
    label_font = _load_font(18, bold=True)
    small_font = _load_font(15, bold=False)
    gate_font = _load_font(16, bold=True)
    draw.text((left_x0 + 150, top + 18), "Long Short-Term Memory (LSTM) Cell", font=title_font, fill="#1f2435")

    core = (left_x0 + 145, top + 135, left_x1 - 140, bottom - 120)
    draw.rounded_rectangle(core, radius=40, fill="#dfdfdf", outline="#2f2f2f", width=3)

    prev_box = (left_x0 + 18, top + 125, left_x0 + 118, bottom - 145)
    next_box = (left_x1 - 118, top + 125, left_x1 - 18, bottom - 145)
    draw.rounded_rectangle(prev_box, radius=28, fill="#f2f2f2", outline="#2f2f2f", width=3)
    draw.rounded_rectangle(next_box, radius=28, fill="#f2f2f2", outline="#2f2f2f", width=3)
    _draw_wrapped_text(draw, "Previous Cell\nc_t-1\n\nPrevious Hidden\nh_t-1", label_font, "#222222", (prev_box[0] + 10, prev_box[1] + 26, prev_box[2] - 10, prev_box[3] - 10), line_spacing=8)
    _draw_wrapped_text(draw, "Future Cell\nc_t+1\n\nFuture Hidden\nh_t+1", label_font, "#222222", (next_box[0] + 10, next_box[1] + 26, next_box[2] - 10, next_box[3] - 10), line_spacing=8)

    top_y = top + 168
    draw.line((prev_box[2], top_y, core[2] - 12, top_y), fill="#222222", width=3)
    _draw_arrow(draw, (core[2] - 12, top_y), (next_box[0], top_y), fill="#222222", width=3, arrow_size=10)

    gate_specs = [
        ("Forget Gate", left_x0 + 255),
        ("Input Gate", left_x0 + 410),
        ("Cell Update", left_x0 + 540),
        ("Output Gate", left_x0 + 675),
    ]
    for name, x in gate_specs:
        gate_box = (x, top + 250, x + 80, top + 320)
        fill = "#9ad65f" if name != "Cell Update" else "#9ad65f"
        label = "σ" if name != "Cell Update" else "tanh"
        draw.rounded_rectangle(gate_box, radius=14, fill=fill, outline="#4a6a2c", width=2)
        _draw_centered_text(draw, ((gate_box[0] + gate_box[2]) / 2, (gate_box[1] + gate_box[3]) / 2), label, gate_font, "#18220f")
        _draw_wrapped_text(draw, name, small_font, "#222222", (x - 10, top + 196, x + 95, top + 240), line_spacing=4)

    mults = [(left_x0 + 292, top + 184), (left_x0 + 448, top + 184), (left_x0 + 720, top + 246)]
    plus = (left_x0 + 500, top + 184)
    for cx, cy in mults:
        draw.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill="#ffa45f", outline="#7a4c26", width=2)
        _draw_centered_text(draw, (cx, cy), "x", label_font, "#3f2206")
    draw.ellipse((plus[0] - 22, plus[1] - 22, plus[0] + 22, plus[1] + 22), fill="#ffa45f", outline="#7a4c26", width=2)
    _draw_centered_text(draw, plus, "+", label_font, "#3f2206")

    x_input = (left_x0 + 185, bottom - 110)
    h_prev = (left_x0 + 305, bottom - 110)
    h_out = (left_x1 - 190, top + 76)
    x_next = (left_x1 - 190, bottom - 110)
    for center, text in [(x_input, "X_t"), (h_prev, "h_t-1"), (h_out, "h_t"), (x_next, "X_t+1")]:
        draw.ellipse((center[0] - 30, center[1] - 30, center[0] + 30, center[1] + 30), fill="#d8c3ee", outline="#8b73a6", width=2)
        _draw_centered_text(draw, center, text, small_font, "#2b2140")

    _draw_arrow(draw, (x_input[0], x_input[1] - 30), (left_x0 + 280, top + 320), fill="#222222", width=2, arrow_size=8)
    _draw_arrow(draw, (h_prev[0], h_prev[1] - 30), (left_x0 + 280, top + 338), fill="#222222", width=2, arrow_size=8)
    _draw_arrow(draw, (plus[0], plus[1] + 22), (left_x0 + 700, top + 270), fill="#222222", width=2, arrow_size=8)
    _draw_arrow(draw, (left_x0 + 720, top + 320), (h_out[0], h_out[1] + 30), fill="#222222", width=2, arrow_size=8)
    _draw_arrow(draw, (next_box[0] + 12, bottom - 145), (x_next[0], x_next[1] - 30), fill="#222222", width=2, arrow_size=8)

    _draw_summary_panel(draw, right_x0, right_x1, title, explanation, overlay_content, footer_text="Deterministic LSTM cell diagram")
    return canvas


def _render_pipeline_card(title, explanation, stage_titles, overlay_content=None, footer_text="Topic-accurate AI diagram"):
    canvas = Image.new("RGB", (PRO_CARD_WIDTH, PRO_CARD_HEIGHT), "#08111f")
    draw = ImageDraw.Draw(canvas)

    title_font = _load_font(38, bold=True)
    section_font = _load_font(22, bold=True)
    body_font = _load_font(21, bold=False)
    small_font = _load_font(18, bold=False)
    stage_font = _load_font(19, bold=True)

    draw.rounded_rectangle(
        [(22, 22), (PRO_CARD_WIDTH - 22, PRO_CARD_HEIGHT - 22)],
        radius=28,
        outline="#173756",
        width=3,
    )

    left_x0 = 48
    left_x1 = int(PRO_CARD_WIDTH * 0.71)
    right_x0 = left_x1 + 34
    right_x1 = PRO_CARD_WIDTH - 44

    draw.text((left_x0, 46), "AI VISUAL WORKFLOW", font=small_font, fill="#57c4ff")
    _draw_wrapped_text(draw, title, title_font, "#f5f8ff", (left_x0, 80, left_x1 - 20, 170))
    _draw_wrapped_text(draw, explanation, body_font, "#c5d8ee", (left_x0, 170, left_x1 - 20, 250))

    diagram_top = 285
    diagram_bottom = PRO_CARD_HEIGHT - 80
    draw.rounded_rectangle(
        [(left_x0, diagram_top), (left_x1, diagram_bottom)],
        radius=26,
        fill="#0d1728",
        outline="#1f476d",
        width=2,
    )

    stage_count = len(stage_titles)
    box_width = 160
    box_height = 92
    usable_width = (left_x1 - left_x0) - 120
    x_gap = usable_width / max(stage_count - 1, 1)
    y_mid = (diagram_top + diagram_bottom) // 2
    boxes = []
    for index, stage_title in enumerate(stage_titles):
        x_center = left_x0 + 60 + index * x_gap
        y_offset = -70 if index % 2 == 0 else 50
        y_center = y_mid + y_offset
        box = (
            int(x_center - box_width / 2),
            int(y_center - box_height / 2),
            int(x_center + box_width / 2),
            int(y_center + box_height / 2),
        )
        boxes.append(box)
        fill = "#13253b" if index % 2 == 0 else "#14314a"
        outline = "#4fc5ff" if index % 2 == 0 else "#7cf6c0"
        _draw_labeled_box(draw, box, stage_title, stage_font, fill, outline, "#eff7ff")

    for index in range(len(boxes) - 1):
        start = (boxes[index][2], (boxes[index][1] + boxes[index][3]) // 2)
        end = (boxes[index + 1][0], (boxes[index + 1][1] + boxes[index + 1][3]) // 2)
        _draw_arrow(draw, start, end, fill="#56d6ff", width=4, arrow_size=12)

    draw.text((right_x0, 54), "English Summary", font=section_font, fill="#9fdcff")
    _draw_wrapped_text(draw, explanation, body_font, "#d8e6ff", (right_x0, 92, right_x1, 225))
    draw.text((right_x0, 255), "Key Points", font=section_font, fill="#9fdcff")

    bullet_y = 295
    bullets = list((overlay_content or {}).get("bullets") or [])
    for bullet in bullets[:4]:
        wrapped_lines = _wrap_text(draw, bullet, body_font, (right_x1 - right_x0) - 24)
        if not wrapped_lines:
            continue
        draw.ellipse([(right_x0, bullet_y + 10), (right_x0 + 10, bullet_y + 20)], fill="#57c4ff")
        draw.text((right_x0 + 22, bullet_y), wrapped_lines[0], font=body_font, fill="#f3f7ff")
        bullet_y += 32
        for extra_line in wrapped_lines[1:]:
            draw.text((right_x0 + 22, bullet_y), extra_line, font=body_font, fill="#c4d8f3")
            bullet_y += 30
        bullet_y += 12

    draw.text((right_x0, PRO_CARD_HEIGHT - 46), footer_text, font=small_font, fill="#6fa4d0")
    return canvas


def _detect_topic_family(prompt):
    prompt_lower = (prompt or "").lower()
    if any(keyword in prompt_lower for keyword in ("bpnn", "backpropagation neural network", "back propagation neural network", "backpropagation")):
        return "bpnn"
    if any(keyword in prompt_lower for keyword in ("cnn", "convolutional neural network")):
        return "cnn"
    if "transformer" in prompt_lower or "self attention" in prompt_lower:
        return "transformer"
    if any(keyword in prompt_lower for keyword in ("rnn", "recurrent neural network")):
        return "rnn"
    if "lstm" in prompt_lower:
        return "lstm"
    if "rag" in prompt_lower or "retrieval augmented generation" in prompt_lower or "retrieval-augmented generation" in prompt_lower:
        return "rag"
    if "bert" in prompt_lower:
        return "bert"
    if "gpt" in prompt_lower:
        return "gpt"
    if any(keyword in prompt_lower for keyword in ("neural network", "neural networks", "ann")):
        return "neural_network"
    if any(keyword in prompt_lower for keyword in ("nlp", "natural language processing", "tokenization", "llm")):
        return "nlp"
    if any(keyword in prompt_lower for keyword in ("deep learning", "autoencoder", "gan")):
        return "dl"
    if any(keyword in prompt_lower for keyword in ("data science", "eda", "analytics", "analysis", "feature engineering", "dashboard")):
        return "ds"
    if any(keyword in prompt_lower for keyword in ("machine learning", "ml", "decision tree", "random forest", "svm", "regression", "classification", "clustering")):
        return "ml"
    return "ai"


def _normalize_reference_name(value):
    normalized = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return normalized or "reference"


def _build_reference_search_query(prompt, topic_family):
    base = (prompt or "").strip()
    family_queries = {
        "cnn": "convolutional neural network architecture diagram",
        "rnn": "recurrent neural network architecture diagram",
        "lstm": "lstm cell architecture diagram",
        "transformer": "transformer architecture diagram self attention",
        "rag": "retrieval augmented generation pipeline diagram",
        "bert": "bert encoder architecture diagram",
        "gpt": "gpt decoder architecture diagram",
        "nlp": "natural language processing pipeline diagram",
        "ml": "machine learning pipeline diagram",
        "ds": "data science workflow diagram",
        "ai": "artificial intelligence system architecture diagram",
    }
    if topic_family in family_queries:
        return family_queries[topic_family]
    return f"{base} diagram"


def _find_local_reference_image(prompt):
    _ensure_reference_dir()
    topic_family = _detect_topic_family(prompt)
    candidates = []
    if topic_family in LOCAL_REFERENCE_MAP:
        candidates.extend(LOCAL_REFERENCE_MAP[topic_family])

    prompt_tokens = set(re.findall(r"[a-z0-9]+", (prompt or "").lower()))
    for entry in os.listdir(REFERENCE_DIR):
        lower_name = entry.lower()
        if lower_name in [name.lower() for name in candidates]:
            return {
                "image_url": f"/reference_library/{entry}",
                "model": "local-reference-library",
                "provider": "local-reference-library",
                "source_label": "Local reference library",
            }
        name_tokens = set(re.findall(r"[a-z0-9]+", lower_name))
        if prompt_tokens and prompt_tokens.intersection(name_tokens):
            return {
                "image_url": f"/reference_library/{entry}",
                "model": "local-reference-library",
                "provider": "local-reference-library",
                "source_label": "Local reference library",
            }
    return None


def _download_reference_from_url(url, prefix):
    response = httpx.get(url, timeout=20, follow_redirects=True)
    response.raise_for_status()
    return _save_downloaded_image(response.content, prefix=prefix)


def _search_reference_with_serpapi(search_query):
    if not SERPAPI_API_KEY:
        return None

    endpoint = (
        "https://serpapi.com/search.json?engine=google_images"
        f"&q={quote(search_query)}&api_key={SERPAPI_API_KEY}"
    )
    response = httpx.get(endpoint, timeout=20, follow_redirects=True)
    response.raise_for_status()
    payload = response.json()
    for item in payload.get("images_results", []):
        image_url = item.get("original") or item.get("thumbnail")
        source_url = item.get("link") or item.get("original")
        if not image_url:
            continue
        try:
            local_url = _download_reference_from_url(image_url, prefix="online-reference")
            return {
                "image_url": local_url,
                "model": "serpapi-google-images",
                "provider": "serpapi-google-images",
                "source_url": source_url,
                "source_label": "Google Images reference",
            }
        except Exception:
            continue
    return None


def _search_reference_with_wikimedia(search_query):
    endpoint = (
        "https://commons.wikimedia.org/w/api.php?action=query&generator=search"
        f"&gsrsearch={quote(search_query)}&gsrnamespace=6&prop=imageinfo"
        "&iiprop=url&iiurlwidth=1600&format=json"
    )
    response = httpx.get(endpoint, timeout=20, follow_redirects=True)
    response.raise_for_status()
    payload = response.json()
    pages = (payload.get("query") or {}).get("pages") or {}
    for page in pages.values():
        imageinfo = (page.get("imageinfo") or [])
        if not imageinfo:
            continue
        image_url = imageinfo[0].get("thumburl") or imageinfo[0].get("url")
        source_url = imageinfo[0].get("descriptionurl") or imageinfo[0].get("url")
        if not image_url:
            continue
        try:
            local_url = _download_reference_from_url(
                image_url,
                prefix=f"wikimedia-{_normalize_reference_name(search_query)}",
            )
            return {
                "image_url": local_url,
                "model": "wikimedia-commons",
                "provider": "wikimedia-commons",
                "source_url": source_url,
                "source_label": "Wikimedia Commons reference",
            }
        except Exception:
            continue
    return None


def _find_online_reference_image(prompt):
    topic_family = _detect_topic_family(prompt)
    search_query = _build_reference_search_query(prompt, topic_family)

    for finder in (_search_reference_with_serpapi, _search_reference_with_wikimedia):
        try:
            result = finder(search_query)
        except Exception:
            result = None
        if result:
            return result
    return None


def _render_end_to_end_neural_network(title, explanation, overlay_content=None, include_backprop=False):
    canvas = Image.new("RGB", (PRO_CARD_WIDTH, PRO_CARD_HEIGHT), "#08111f")
    draw = ImageDraw.Draw(canvas)

    title_font = _load_font(38, bold=True)
    section_font = _load_font(22, bold=True)
    body_font = _load_font(21, bold=False)
    small_font = _load_font(18, bold=False)
    label_font = _load_font(19, bold=True)
    node_font = _load_font(16, bold=False)

    draw.rounded_rectangle(
        [(22, 22), (PRO_CARD_WIDTH - 22, PRO_CARD_HEIGHT - 22)],
        radius=28,
        outline="#173756",
        width=3,
    )

    left_x0 = 48
    left_x1 = int(PRO_CARD_WIDTH * 0.71)
    right_x0 = left_x1 + 34
    right_x1 = PRO_CARD_WIDTH - 44

    draw.text((left_x0, 46), "AI ARCHITECTURE VISUAL", font=small_font, fill="#57c4ff")
    _draw_wrapped_text(draw, title, title_font, "#f5f8ff", (left_x0, 80, left_x1 - 20, 170))
    _draw_wrapped_text(draw, explanation, body_font, "#c5d8ee", (left_x0, 170, left_x1 - 20, 255))

    diagram_top = 275
    diagram_bottom = PRO_CARD_HEIGHT - 78
    diagram_left = left_x0
    diagram_right = left_x1
    draw.rounded_rectangle(
        [(diagram_left, diagram_top), (diagram_right, diagram_bottom)],
        radius=26,
        fill="#0d1728",
        outline="#1f476d",
        width=2,
    )

    layer_xs = [
        diagram_left + 90,
        diagram_left + 300,
        diagram_left + 510,
        diagram_left + 720,
    ]
    layer_specs = [
        ("Input Layer", 4, "#46c2ff"),
        ("Hidden Layer 1", 5, "#62d0ff"),
        ("Hidden Layer 2", 4, "#62d0ff"),
        ("Output Layer", 2, "#7cf6c0"),
    ]
    y_top = diagram_top + 125
    y_bottom = diagram_bottom - 80
    node_radius = 18
    layer_nodes = []

    for layer_index, (layer_name, node_count, color) in enumerate(layer_specs):
        x = layer_xs[layer_index]
        draw.text((x - 60, diagram_top + 34), layer_name, font=label_font, fill="#bfe8ff")
        nodes = []
        for node_index in range(node_count):
            if node_count == 1:
                y = (y_top + y_bottom) / 2
            else:
                y = y_top + (node_index * (y_bottom - y_top) / (node_count - 1))
            center = (x, y)
            nodes.append(center)
        layer_nodes.append((color, nodes))

    for layer_index in range(len(layer_nodes) - 1):
        source_color, source_nodes = layer_nodes[layer_index]
        target_color, target_nodes = layer_nodes[layer_index + 1]
        for source_node in source_nodes:
            for target_node in target_nodes:
                _draw_arrow(
                    draw,
                    (source_node[0] + node_radius, source_node[1]),
                    (target_node[0] - node_radius, target_node[1]),
                    fill="#2ea7ea",
                    width=2,
                    arrow_size=8,
                )

    for color, nodes in layer_nodes:
        for index, center in enumerate(nodes, start=1):
            draw.ellipse(
                [
                    (center[0] - node_radius, center[1] - node_radius),
                    (center[0] + node_radius, center[1] + node_radius),
                ],
                fill=color,
                outline="#e8fbff",
                width=2,
            )
            _draw_centered_text(draw, center, str(index), node_font, "#062135")

    draw.text((diagram_left + 42, diagram_bottom - 44), "Forward pass", font=label_font, fill="#56d6ff")
    _draw_arrow(
        draw,
        (diagram_left + 170, diagram_bottom - 34),
        (diagram_right - 90, diagram_bottom - 34),
        fill="#56d6ff",
        width=4,
        arrow_size=12,
    )

    if include_backprop:
        draw.text((diagram_left + 42, diagram_top + 72), "Backpropagation error flow", font=label_font, fill="#ff8e7d")
        _draw_arrow(
            draw,
            (diagram_right - 90, diagram_top + 74),
            (diagram_left + 210, diagram_top + 74),
            fill="#ff8e7d",
            width=4,
            arrow_size=12,
            dashed=True,
        )
        update_box = (diagram_left + 600, diagram_top + 28, diagram_left + 880, diagram_top + 120)
        draw.rounded_rectangle(update_box, radius=16, fill="#3a1820", outline="#ff8e7d", width=2)
        _draw_wrapped_text(draw, "Loss -> Gradients -> Weight Update", body_font, "#ffe1dc", (update_box[0] + 16, update_box[1] + 16, update_box[2] - 16, update_box[3] - 12), line_spacing=4)

    draw.text((right_x0, 54), "English Summary", font=section_font, fill="#9fdcff")
    _draw_wrapped_text(draw, explanation, body_font, "#d8e6ff", (right_x0, 92, right_x1, 230))

    draw.text((right_x0, 260), "Key Points", font=section_font, fill="#9fdcff")
    bullet_y = 300
    bullets = list((overlay_content or {}).get("bullets") or [])
    for bullet in bullets[:4]:
        wrapped_lines = _wrap_text(draw, bullet, body_font, (right_x1 - right_x0) - 24)
        if not wrapped_lines:
            continue
        draw.ellipse([(right_x0, bullet_y + 10), (right_x0 + 10, bullet_y + 20)], fill="#57c4ff")
        draw.text((right_x0 + 22, bullet_y), wrapped_lines[0], font=body_font, fill="#f3f7ff")
        bullet_y += 32
        for extra_line in wrapped_lines[1:]:
            draw.text((right_x0 + 22, bullet_y), extra_line, font=body_font, fill="#c4d8f3")
            bullet_y += 30
        bullet_y += 12

    footer_text = "End-to-end neural network diagram"
    if include_backprop:
        footer_text = "End-to-end neural network with backpropagation"
    draw.text((right_x0, PRO_CARD_HEIGHT - 46), footer_text, font=small_font, fill="#6fa4d0")
    return canvas


def _render_ai_diagram_image(title, explanation, mermaid_text, overlay_content=None):
    canvas = Image.new("RGB", (PRO_CARD_WIDTH, PRO_CARD_HEIGHT), "#08111f")
    draw = ImageDraw.Draw(canvas)

    title_font = _load_font(40, bold=True)
    section_font = _load_font(22, bold=True)
    body_font = _load_font(21, bold=False)
    small_font = _load_font(18, bold=False)

    draw.rounded_rectangle(
        [(22, 22), (PRO_CARD_WIDTH - 22, PRO_CARD_HEIGHT - 22)],
        radius=28,
        outline="#173756",
        width=3,
    )

    left_x0 = 48
    left_x1 = int(PRO_CARD_WIDTH * 0.7)
    right_x0 = left_x1 + 34
    right_x1 = PRO_CARD_WIDTH - 44

    draw.text((left_x0, 46), "AI ARCHITECTURE VISUAL", font=small_font, fill="#57c4ff")
    _draw_wrapped_text(draw, title, title_font, "#f5f8ff", (left_x0, 80, left_x1 - 20, 170))
    _draw_wrapped_text(draw, explanation, body_font, "#c5d8ee", (left_x0, 170, left_x1 - 20, 260))

    diagram_top = 280
    diagram_bottom = PRO_CARD_HEIGHT - 70
    draw.rounded_rectangle(
        [(left_x0, diagram_top), (left_x1, diagram_bottom)],
        radius=26,
        fill="#0d1728",
        outline="#1f476d",
        width=2,
    )

    node_map, edges = _parse_mermaid_nodes_and_edges(mermaid_text)
    node_ids = list(node_map.keys())
    layers = _layout_layers(node_ids, edges) if node_ids else []
    positions = {}

    if layers:
        layer_count = max(len(layers), 1)
        usable_width = (left_x1 - left_x0) - 120
        usable_height = (diagram_bottom - diagram_top) - 100
        node_width = min(220, max(150, usable_width // max(layer_count, 2)))
        node_height = 72

        for layer_index, layer in enumerate(layers):
            x_center = left_x0 + 60 + int(layer_index * (usable_width / max(layer_count - 1, 1)))
            count = len(layer)
            for node_index, node_id in enumerate(layer):
                y_center = diagram_top + 60 + int((node_index + 1) * (usable_height / (count + 1)))
                positions[node_id] = (x_center, y_center)

        for source_id, target_id in edges:
            if source_id not in positions or target_id not in positions:
                continue
            x1, y1 = positions[source_id]
            x2, y2 = positions[target_id]
            start = (x1 + node_width // 2 - 10, y1)
            end = (x2 - node_width // 2 + 10, y2)
            draw.line([start, end], fill="#57c4ff", width=4)
            arrow_size = 10
            draw.polygon(
                [
                    (end[0], end[1]),
                    (end[0] - arrow_size, end[1] - arrow_size // 2),
                    (end[0] - arrow_size, end[1] + arrow_size // 2),
                ],
                fill="#57c4ff",
            )

        for node_id, (x_center, y_center) in positions.items():
            x0 = x_center - node_width // 2
            y0 = y_center - node_height // 2
            x1 = x_center + node_width // 2
            y1 = y_center + node_height // 2
            draw.rounded_rectangle(
                [(x0, y0), (x1, y1)],
                radius=20,
                fill="#13253b",
                outline="#4fc5ff",
                width=3,
            )
            _draw_wrapped_text(
                draw,
                node_map.get(node_id, node_id),
                body_font,
                "#eff7ff",
                (x0 + 16, y0 + 12, x1 - 16, y1 - 10),
                line_spacing=4,
            )

    draw.text((right_x0, 54), "English Summary", font=section_font, fill="#9fdcff")
    _draw_wrapped_text(draw, explanation, body_font, "#d8e6ff", (right_x0, 92, right_x1, 220))

    draw.text((right_x0, 250), "Key Points", font=section_font, fill="#9fdcff")
    bullet_y = 290
    bullets = list((overlay_content or {}).get("bullets") or [])
    for bullet in bullets[:4]:
        wrapped_lines = _wrap_text(draw, bullet, body_font, (right_x1 - right_x0) - 24)
        if not wrapped_lines:
            continue
        draw.ellipse([(right_x0, bullet_y + 10), (right_x0 + 10, bullet_y + 20)], fill="#57c4ff")
        draw.text((right_x0 + 22, bullet_y), wrapped_lines[0], font=body_font, fill="#f3f7ff")
        bullet_y += 32
        for extra_line in wrapped_lines[1:]:
            draw.text((right_x0 + 22, bullet_y), extra_line, font=body_font, fill="#c4d8f3")
            bullet_y += 30
        bullet_y += 12

    draw.text((right_x0, PRO_CARD_HEIGHT - 46), "Topic-accurate AI diagram", font=small_font, fill="#6fa4d0")
    return canvas


def _generate_topic_diagram_image(prompt, overlay_content=None):
    topic_family = _detect_topic_family(prompt)

    if topic_family == "cnn":
        diagram_image = _render_cnn_architecture_diagram(
            "CNN Architecture",
            "This diagram shows convolution, activation, pooling, flattening, and fully connected classification stages in a typical CNN.",
            overlay_content=overlay_content,
        )
    elif topic_family == "rnn":
        diagram_image = _render_rnn_unrolled_diagram(
            "RNN Unrolled Architecture",
            "This diagram shows how a recurrent neural network reuses the hidden state across sequential time steps during forward processing.",
            overlay_content=overlay_content,
        )
    elif topic_family == "lstm":
        diagram_image = _render_lstm_cell_diagram(
            "LSTM Cell Architecture",
            "This diagram shows the forget gate, input gate, cell update, and output gate that control information flow through an LSTM cell.",
            overlay_content=overlay_content,
        )
    elif topic_family == "bpnn":
        diagram_image = _render_end_to_end_neural_network(
            "Backpropagation Neural Network (BPNN) Architecture",
            "A BPNN starts with input features, pushes them through one or more hidden layers, computes an output, then sends the error backward to update weights and biases.",
            overlay_content=overlay_content,
            include_backprop=True,
        )
    elif topic_family == "neural_network":
        diagram_image = _render_end_to_end_neural_network(
            "Neural Network Architecture",
            "A neural network transforms input features through hidden layers, combines weighted signals, and produces final outputs.",
            overlay_content=overlay_content,
            include_backprop=False,
        )
    elif topic_family == "transformer":
        diagram_image = _render_pipeline_card(
            "Transformer Architecture",
            "This visual shows token embeddings, positional encoding, self-attention computation, residual normalization, feed-forward blocks, and output logits.",
            ["Tokens", "Embeddings", "Q / K / V", "Self-Attention", "Add + Norm", "Feed Forward", "Output"],
            overlay_content=overlay_content,
            footer_text="Topic-specialized transformer diagram",
        )
    elif topic_family == "rag":
        diagram_image = _render_pipeline_card(
            "RAG Pipeline",
            "This visual shows query embedding, vector retrieval, passage selection, prompt assembly, and grounded LLM answer generation.",
            ["User Query", "Embedding", "Vector Search", "Top-k Passages", "Prompt", "LLM Answer"],
            overlay_content=overlay_content,
            footer_text="Topic-specialized RAG diagram",
        )
    elif topic_family == "bert":
        diagram_image = _render_pipeline_card(
            "BERT Encoder Stack",
            "This visual shows tokenization, embeddings, encoder blocks, contextual token representations, and downstream task heads.",
            ["Tokenize", "Embeddings", "Encoder 1", "Encoder 2", "Context Vectors", "Task Head"],
            overlay_content=overlay_content,
            footer_text="Topic-specialized BERT diagram",
        )
    elif topic_family == "gpt":
        diagram_image = _render_pipeline_card(
            "GPT Decoder Stack",
            "This visual shows prompt tokens, masked self-attention, decoder blocks, next-token logits, and autoregressive text generation.",
            ["Prompt", "Embeddings", "Masked Attention", "Decoder Block", "Logits", "Next Token"],
            overlay_content=overlay_content,
            footer_text="Topic-specialized GPT diagram",
        )
    elif topic_family == "nlp":
        diagram_image = _render_pipeline_card(
            "NLP System Pipeline",
            "This visual shows how text moves through preprocessing, tokenization, embeddings, model understanding, and final NLP output.",
            ["Raw Text", "Clean + Tokenize", "Embeddings", "Language Model", "Task Output"],
            overlay_content=overlay_content,
            footer_text="Topic-specialized NLP diagram",
        )
    elif topic_family == "dl":
        diagram_image = _render_pipeline_card(
            "Deep Learning Workflow",
            "This visual shows deep learning from input data through feature learning, hidden representations, optimization, and final prediction.",
            ["Input Data", "Feature Extraction", "Hidden Layers", "Loss + Optimizer", "Prediction"],
            overlay_content=overlay_content,
            footer_text="Topic-specialized deep learning diagram",
        )
    elif topic_family == "ds":
        diagram_image = _render_pipeline_card(
            "Data Science Workflow",
            "This visual shows a complete data science pipeline from collecting data to cleaning, analysis, modeling, and communicating insights.",
            ["Collect Data", "Clean Data", "Explore + Analyze", "Model", "Insights"],
            overlay_content=overlay_content,
            footer_text="Topic-specialized data science diagram",
        )
    elif topic_family == "ml":
        diagram_image = _render_pipeline_card(
            "Machine Learning Pipeline",
            "This visual shows machine learning from data preparation through feature engineering, training, evaluation, and prediction.",
            ["Dataset", "Preprocess", "Train Model", "Evaluate", "Predict"],
            overlay_content=overlay_content,
            footer_text="Topic-specialized machine learning diagram",
        )
    elif topic_family == "ai":
        diagram_image = _render_pipeline_card(
            "Artificial Intelligence System",
            "This visual shows a general AI pipeline connecting data, learning algorithms, reasoning, deployment, and real-world decisions.",
            ["Input Data", "Learning", "Knowledge", "Inference", "Decision"],
            overlay_content=overlay_content,
            footer_text="Topic-specialized AI diagram",
        )
    else:
        architecture = generate_architecture(prompt)
        title = architecture.get("title", "AI Diagram")
        explanation = architecture.get("explanation", "")
        mermaid = architecture.get("mermaid", "")
        diagram_image = _render_ai_diagram_image(
            title,
            explanation,
            mermaid,
            overlay_content=overlay_content,
        )
    image_url = _save_image(diagram_image)
    return {
        "image_url": image_url,
        "model": "local-ai-diagram",
        "provider": "local-ai-diagram",
    }


def get_image_status():
    if IMAGE_PROVIDER != "flux":
        return {
            "ready": False,
            "provider": IMAGE_PROVIDER,
            "model": HF_IMAGE_MODEL,
            "message": "Set IMAGE_PROVIDER=flux in .env to use Flux image generation.",
        }

    if not HF_TOKEN:
        return {
            "ready": False,
            "provider": "flux",
            "model": HF_IMAGE_MODEL,
            "message": "HF_TOKEN is missing in .env, so Flux image generation cannot start.",
        }

    return {
        "ready": True,
        "provider": "flux",
        "model": HF_IMAGE_MODEL,
        "message": (
            f"Hybrid image mode is enabled: local reference library first, online reference search next, "
            f"and Flux or deterministic diagram generation as fallback using '{HF_IMAGE_MODEL}'."
        ),
    }


def _client():
    return InferenceClient(provider=HF_PROVIDER, api_key=HF_TOKEN)


def _request_flux_image(prompt):
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN is missing in the .env file.")

    client = _client()

    negative_prompt = (
        "text, words, letters, typography, caption, labels, subtitles, watermark, "
        "signature, logo, handwritten text, gibberish, foreign language, german text"
    )
    inference_steps = max(FLUX_STEPS, 20)

    try:
        image = client.text_to_image(
            prompt=prompt,
            model=HF_IMAGE_MODEL,
            width=FLUX_WIDTH,
            height=FLUX_HEIGHT,
            num_inference_steps=inference_steps,
            guidance_scale=FLUX_GUIDANCE_SCALE,
            negative_prompt=negative_prompt,
        )
    except TypeError:
        try:
            image = client.text_to_image(
                prompt=prompt,
                model=HF_IMAGE_MODEL,
                negative_prompt=negative_prompt,
            )
        except TypeError:
            image = client.text_to_image(
                prompt=prompt,
                model=HF_IMAGE_MODEL,
            )
    except Exception as exc:
        raise RuntimeError(f"Flux image generation failed: {exc}") from exc

    if isinstance(image, Image.Image):
        return image
    return Image.open(io.BytesIO(image))


def _generate_with_flux(prompt):
    output_image = _request_flux_image(prompt)

    image_url = _save_image(output_image)
    return {
        "image_url": image_url,
        "model": HF_IMAGE_MODEL,
        "provider": "flux",
    }


def generate_image(prompt, image_prompt=None, overlay_content=None):
    clean_prompt = (prompt or "").strip()
    final_prompt = (image_prompt or prompt or "").strip()

    if not final_prompt:
        raise RuntimeError("Please enter an image prompt first.")

    if IMAGE_PROVIDER != "flux":
        raise RuntimeError("IMAGE_PROVIDER must be set to 'flux' in the .env file.")

    local_reference = _find_local_reference_image(clean_prompt or final_prompt)
    if local_reference:
        local_reference["caption"] = f"Here is a reference image for: {clean_prompt}"
        local_reference["image_prompt"] = final_prompt
        return local_reference

    online_reference = _find_online_reference_image(clean_prompt or final_prompt)
    if online_reference:
        online_reference["caption"] = f"Here is an online reference image for: {clean_prompt}"
        online_reference["image_prompt"] = final_prompt
        return online_reference

    topic_family = _detect_topic_family(clean_prompt or final_prompt)
    deterministic_families = {
        "cnn", "rnn", "lstm", "bpnn", "neural_network",
        "transformer", "rag", "bert", "gpt", "nlp", "ml", "ds", "ai", "dl"
    }
    if topic_family in deterministic_families:
        result = _generate_topic_diagram_image(clean_prompt or final_prompt, overlay_content=overlay_content)
        result["caption"] = f"Here is an AI-topic image for: {clean_prompt}"
        result["image_prompt"] = final_prompt
        return result

    generated_image = _request_flux_image(final_prompt)
    output_image = generated_image
    if overlay_content:
        output_image = _compose_guided_flux_card(
            generated_image,
            clean_prompt or final_prompt,
            overlay_content=overlay_content,
        )

    image_url = _save_image(output_image)
    result = {
        "image_url": image_url,
        "model": HF_IMAGE_MODEL,
        "provider": "flux",
    }
    result["caption"] = f"Here is an AI-topic image for: {clean_prompt}"
    result["image_prompt"] = final_prompt
    return result
