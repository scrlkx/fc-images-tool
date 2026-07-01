figma.showUI(__html__, { width: 400, height: 370 });

figma.ui.postMessage({
  type: "pages",
  pages: figma.root.children.map((p) => p.name),
});

const SLIDE_W = 1080;
const SLIDE_H = 1440;
const GAP = 100;

function progress(text) {
  figma.ui.postMessage({ type: "progress", text });
}

function findByName(node, name) {
  if (node.name === name) return node;
  if ("children" in node) {
    for (const child of node.children) {
      const found = findByName(child, name);
      if (found) return found;
    }
  }
  return null;
}

function findImageNode(node) {
  if ("fills" in node && Array.isArray(node.fills) && node.fills.some((f) => f.type === "IMAGE")) {
    return node;
  }
  if ("children" in node) {
    for (const child of node.children) {
      const found = findImageNode(child);
      if (found) return found;
    }
  }
  return null;
}

function base64ToUint8Array(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

function replaceProductImage(coverNode, dataUrl) {
  const base64 = dataUrl.split(",")[1];
  const bytes = base64ToUint8Array(base64);
  const image = figma.createImage(bytes);
  const imageNode = findImageNode(coverNode);
  if (!imageNode) return;
  const fills = imageNode.fills.map((f) => {
    if (f.type === "IMAGE") return Object.assign({}, f, { imageHash: image.hash, scaleMode: "FIT" });
    return f;
  });
  imageNode.fills = fills;
}

async function updateSlide2(slide2Clone, product) {
  // Cover image
  const cover = findByName(slide2Clone, "Cover");
  if (cover) replaceProductImage(cover, product.image_b64);

  // Product name — first child of Details
  const details = findByName(slide2Clone, "Details");
  if (details && details.children.length > 0) {
    const nameNode = details.children[0];
    if (nameNode.type === "TEXT") {
      nameNode.characters = product.name;
    }
  }

  // Price nodes — children of Price
  const price = findByName(slide2Clone, "Price");
  if (price && price.children.length >= 2) {
    const prevNode = price.children[0];
    const newNode = price.children[1];

    if (prevNode.type === "TEXT") {
      const prevText = `de R$ ${product.prev_price} por apenas`;
      prevNode.characters = prevText;
      const strikeEnd = `de R$ ${product.prev_price}`.length;
      prevNode.setRangeTextDecoration(0, strikeEnd, "STRIKETHROUGH");
      prevNode.setRangeTextDecoration(strikeEnd, prevText.length, "NONE");
    }

    if (newNode.type === "TEXT") {
      newNode.characters = `R$ ${product.new_price}`;
    }
  }
}

figma.ui.onmessage = async (msg) => {
  if (msg.type === "get_frames") {
    const page = figma.root.children.find((p) => p.name === msg.page_name);
    if (!page) { figma.ui.postMessage({ type: "frames", frames: [] }); return; }
    await page.loadAsync();
    const containerName = msg.mode === "instagram" ? "Instagram" : "Flyers";
    const container = page.children.find((c) => c.name === containerName);
    if (!container) { figma.ui.postMessage({ type: "frames", frames: [] }); return; }
    const frames = container.children.filter((c) => c.type === "FRAME").map((c) => c.name);
    figma.ui.postMessage({ type: "frames", frames });
    return;
  }

  if (msg.type !== "generate") return;

  const payload = msg.payload;

  try {
    // 1. Find target page
    const pageName = msg.page_name;
    progress(`Searching for page "${pageName}"…`);
    const page = figma.root.children.find((p) => p.name === pageName);
    if (!page) throw new Error(`Page "${pageName}" not found.`);
    await page.loadAsync();

    // 2. Find container (Instagram or Flyers)
    const containerName = msg.mode === "instagram" ? "Instagram" : "Flyers";
    const container = page.children.find((c) => c.name === containerName);
    if (!container) throw new Error(`Container "${containerName}" not found on page.`);

    // 3. Get template frame selected by the user (inside the container)
    const templateFrame = container.children.find((c) => c.type === "FRAME" && c.name === msg.frame_name);
    if (!templateFrame) throw new Error(`Frame "${msg.frame_name}" not found in "${containerName}".`);

    const slide1Template = templateFrame.children.find((c) => c.name === "Slide 1");
    if (!slide1Template) throw new Error('Slide 1 not found in the template frame.');

    const slide2Template = templateFrame.children.find((c) => c.name === "Slide 2");
    if (!slide2Template) throw new Error('Slide 2 not found in the template frame.');

    // 4. Load fonts
    progress("Loading fonts…");
    await Promise.all([
      figma.loadFontAsync({ family: "DM Sans", style: "Regular" }),
      figma.loadFontAsync({ family: "DM Sans", style: "Black" }),
    ]);

    // 5. Switch to target page and create parent frame inside the container
    await figma.setCurrentPageAsync(page);

    const parentFrame = figma.createFrame();
    parentFrame.name = payload.frame_name;
    parentFrame.resize(
      (payload.products.length + 1) * SLIDE_W + payload.products.length * GAP,
      SLIDE_H
    );
    parentFrame.fills = [];
    parentFrame.clipsContent = false;
    container.appendChild(parentFrame);

    if (msg.mode === "flyer") {
      parentFrame.layoutMode = "HORIZONTAL";
      parentFrame.itemSpacing = GAP;
      parentFrame.primaryAxisSizingMode = "AUTO";
      parentFrame.counterAxisSizingMode = "AUTO";
    }

    // Position below the last existing frame inside the container
    const existingFrames = container.children.filter((c) => c.type === "FRAME" && c !== parentFrame);
    if (existingFrames.length > 0) {
      const last = existingFrames[existingFrames.length - 1];
      parentFrame.x = last.x;
      parentFrame.y = last.y + last.height + 2000;
    }

    // 6. Clone Slide 1 → update validity text (Instagram only — Flyer has no cover slide)
    if (msg.mode !== "flyer") {
      progress("Creating Slide 1…");
      const slide1Clone = slide1Template.clone();
      parentFrame.appendChild(slide1Clone);
      slide1Clone.x = 0;
      slide1Clone.y = 0;

      const rules1 = findByName(slide1Clone, "Rules 1");
      if (rules1 && rules1.type === "TEXT") {
        rules1.characters = payload.validity_text;
      }
    }

    // 7. Clone Slide 2 for each product
    for (let i = 0; i < payload.products.length; i++) {
      const product = payload.products[i];
      progress(`Creating slide ${i + 1}/${payload.products.length}: ${product.name}…`);

      const slide2Clone = slide2Template.clone();
      parentFrame.appendChild(slide2Clone);
      slide2Clone.x = msg.mode === "flyer" ? i * (SLIDE_W + GAP) : (i + 1) * (SLIDE_W + GAP);
      slide2Clone.y = 0;

      await updateSlide2(slide2Clone, product);
    }

    // 8. Scroll to new frame
    figma.viewport.scrollAndZoomIntoView([parentFrame]);

    figma.ui.postMessage({
      type: "done",
      text: `${payload.products.length} slide(s) generated — frame "${payload.frame_name}"`,
    });
  } catch (err) {
    figma.ui.postMessage({ type: "error", text: err.message });
  }
};
