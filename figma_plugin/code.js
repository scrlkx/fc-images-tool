figma.showUI(__html__, { width: 400, height: 500 });

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
  if (
    "fills" in node &&
    Array.isArray(node.fills) &&
    node.fills.some((f) => f.type === "IMAGE")
  ) {
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
    if (f.type === "IMAGE")
      return Object.assign({}, f, { imageHash: image.hash, scaleMode: "FIT" });
    return f;
  });
  imageNode.fills = fills;
}

function copyImageFill(sourceCoverNode, destCoverNode) {
  const sourceImageNode = findImageNode(sourceCoverNode);
  const destImageNode = findImageNode(destCoverNode);
  if (!sourceImageNode || !destImageNode) return;
  destImageNode.fills = sourceImageNode.fills;
}

async function loadFontsForTextNode(node) {
  if (!node.characters.length) return;
  const fonts = new Set(
    node
      .getStyledTextSegments(["fontName"])
      .map((s) => JSON.stringify(s.fontName)),
  );
  await Promise.all([...fonts].map((f) => figma.loadFontAsync(JSON.parse(f))));
}

// Copies only the text value, not styling — the destination keeps whatever
// style is already defined on it (e.g. the Flyer component's own strikethrough).
async function copyTextValue(sourceNode, destNode) {
  if (
    !sourceNode ||
    !destNode ||
    sourceNode.type !== "TEXT" ||
    destNode.type !== "TEXT"
  )
    return;
  await loadFontsForTextNode(destNode);
  destNode.characters = sourceNode.characters;
}

// Copies live Cover/Details/Price values from an already-generated Instagram
// slide into a Flyer instance, preserving manual edits made directly in Figma.
async function copyProductVisuals(sourceSlide, destSlide) {
  const sourceCover = findByName(sourceSlide, "Cover");
  const destCover = findByName(destSlide, "Cover");
  if (sourceCover && destCover) copyImageFill(sourceCover, destCover);

  const sourceDetails = findByName(sourceSlide, "Details");
  const destDetails = findByName(destSlide, "Details");
  if (
    sourceDetails &&
    destDetails &&
    sourceDetails.children.length > 0 &&
    destDetails.children.length > 0
  ) {
    await copyTextValue(sourceDetails.children[0], destDetails.children[0]);
  }

  const sourcePrice = findByName(sourceSlide, "Price");
  const destPrice = findByName(destSlide, "Price");
  if (
    sourcePrice &&
    destPrice &&
    sourcePrice.children.length >= 2 &&
    destPrice.children.length >= 2
  ) {
    await copyTextValue(sourcePrice.children[0], destPrice.children[0]);
    await copyTextValue(sourcePrice.children[1], destPrice.children[1]);
  }
}

function formatShortDate(dateStr) {
  const [y, m, d] = dateStr.split("-");
  return `${d}/${m}`;
}

const MONTHS_PT = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];

function formatFrameName(dateStr) {
  const [y, m, d] = dateStr.split("-").map(Number);
  return `${d} de ${MONTHS_PT[m - 1]}`;
}

function substituteDateToken(instance, dateStr) {
  const rules1 = findByName(instance, "Rules 1");
  if (rules1 && rules1.type === "TEXT") {
    rules1.characters = rules1.characters.replace(
      "%date%",
      formatShortDate(dateStr),
    );
  }
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

function buildPageStatus() {
  const page = figma.currentPage;

  const findContainer = (name) => page.children.find((c) => c.name === name);
  const componentsContainer = findContainer("Components");
  const instagramContainer = findContainer("Instagram");
  const flyersContainer = findContainer("Flyers");

  const hasComponent = (name) =>
    !!(
      componentsContainer &&
      componentsContainer.children.find(
        (c) => c.type === "COMPONENT" && c.name === name,
      )
    );

  const instagramFrames = instagramContainer
    ? instagramContainer.children
        .filter((c) => c.type === "FRAME")
        .map((c) => c.name)
    : [];

  return {
    type: "page_status",
    pageName: page.name,
    hasComponentsContainer: !!componentsContainer,
    hasInstagramContainer: !!instagramContainer,
    hasFlyersContainer: !!flyersContainer,
    hasInstagramCover: hasComponent("Instagram Cover"),
    hasInstagramSlide: hasComponent("Instagram Slide"),
    hasFlyerComponent: hasComponent("Flyer"),
    instagramFrames,
  };
}

function sendPageStatus() {
  figma.ui.postMessage(buildPageStatus());
}

sendPageStatus();
figma.on("currentpagechange", sendPageStatus);

figma.ui.onmessage = async (msg) => {
  if (msg.type !== "generate") return;

  const payload = msg.payload;
  const isFlyer = msg.mode === "flyer";

  try {
    // 1. Always operate on the currently active page — dynamic-page access
    // guarantees it is already loaded, so no loadAsync() is needed.
    const page = figma.currentPage;

    // 2. Find containers — Flyer reads from "Instagram" and writes into "Flyers".
    let sourceContainer, destContainer;
    if (isFlyer) {
      sourceContainer = page.children.find((c) => c.name === "Instagram");
      if (!sourceContainer)
        throw new Error('Container "Instagram" not found on page.');
      destContainer = page.children.find((c) => c.name === "Flyers");
      if (!destContainer)
        throw new Error('Container "Flyers" not found on page.');
    } else {
      destContainer = page.children.find((c) => c.name === "Instagram");
      if (!destContainer)
        throw new Error('Container "Instagram" not found on page.');
    }

    // 3. Get slide sources: fixed components for Instagram, or the Flyer
    // component + the product slides of a selected source Instagram frame.
    const componentsContainer = page.children.find(
      (c) => c.name === "Components",
    );
    if (!componentsContainer)
      throw new Error('Container "Components" not found on page.');

    let coverComponent, slideComponent, flyerComponent, sourceProductSlides;

    if (!isFlyer) {
      coverComponent = componentsContainer.children.find(
        (c) => c.type === "COMPONENT" && c.name === "Instagram Cover",
      );
      if (!coverComponent)
        throw new Error(
          'Component "Instagram Cover" not found in "Components".',
        );

      slideComponent = componentsContainer.children.find(
        (c) => c.type === "COMPONENT" && c.name === "Instagram Slide",
      );
      if (!slideComponent)
        throw new Error(
          'Component "Instagram Slide" not found in "Components".',
        );
    } else {
      flyerComponent = componentsContainer.children.find(
        (c) => c.type === "COMPONENT" && c.name === "Flyer",
      );
      if (!flyerComponent)
        throw new Error('Component "Flyer" not found in "Components".');

      const sourceFrame = sourceContainer.children.find(
        (c) => c.type === "FRAME" && c.name === msg.frame_name,
      );
      if (!sourceFrame)
        throw new Error(`Frame "${msg.frame_name}" not found in "Instagram".`);

      // Identify product slides by structure (has a "Details" or "Price" sub-node)
      // rather than by node type/position — a slide may have been detached from
      // its component during manual edits, turning it from INSTANCE into FRAME.
      sourceProductSlides = sourceFrame.children.filter(
        (c) =>
          "children" in c &&
          (findByName(c, "Details") || findByName(c, "Price")),
      );
      if (sourceProductSlides.length === 0)
        throw new Error("No product slides found in the selected frame.");
    }

    // 4. Load fonts
    progress("Loading fonts…");
    await Promise.all([
      figma.loadFontAsync({ family: "DM Sans", style: "Regular" }),
      figma.loadFontAsync({ family: "DM Sans", style: "Black" }),
    ]);

    // 5. Create parent frame inside the destination container
    const productCount = isFlyer
      ? sourceProductSlides.length
      : payload.products.length;
    const newFrameName = formatFrameName(msg.from_date);

    const parentFrame = figma.createFrame();
    parentFrame.name = newFrameName;
    parentFrame.resize(
      (productCount + 1) * SLIDE_W + productCount * GAP,
      SLIDE_H,
    );
    parentFrame.fills = [];
    parentFrame.clipsContent = false;
    destContainer.appendChild(parentFrame);

    parentFrame.layoutMode = "HORIZONTAL";
    parentFrame.itemSpacing = GAP;
    parentFrame.primaryAxisSizingMode = "AUTO";
    parentFrame.counterAxisSizingMode = "AUTO";

    // Position below the last existing frame inside the destination container
    const existingFrames = destContainer.children.filter(
      (c) => c.type === "FRAME" && c !== parentFrame,
    );
    if (existingFrames.length > 0) {
      const last = existingFrames[existingFrames.length - 1];
      parentFrame.x = last.x;
      parentFrame.y = last.y + last.height + 2000;
    }

    // 6. Create Slide 1 → update validity text (Instagram only — Flyer has no cover slide)
    if (!isFlyer) {
      progress("Creating Slide 1…");
      const slide1Instance = coverComponent.createInstance();
      parentFrame.appendChild(slide1Instance);
      slide1Instance.name = "Cover";
      slide1Instance.x = 0;
      slide1Instance.y = 0;

      if (msg.validity_date)
        substituteDateToken(slide1Instance, msg.validity_date);
    }

    // 7. Create Slide 2 for each product
    for (let i = 0; i < productCount; i++) {
      const slide2Instance = isFlyer
        ? flyerComponent.createInstance()
        : slideComponent.createInstance();
      parentFrame.appendChild(slide2Instance);
      slide2Instance.name = `Product ${i + 1}`;
      slide2Instance.x = isFlyer
        ? i * (SLIDE_W + GAP)
        : (i + 1) * (SLIDE_W + GAP);
      slide2Instance.y = 0;

      if (isFlyer) {
        progress(`Creating flyer ${i + 1}/${productCount}…`);
        await copyProductVisuals(sourceProductSlides[i], slide2Instance);
        if (msg.validity_date)
          substituteDateToken(slide2Instance, msg.validity_date);
      } else {
        const product = payload.products[i];
        progress(`Creating slide ${i + 1}/${productCount}: ${product.name}…`);
        await updateSlide2(slide2Instance, product);
      }
    }

    // 8. Scroll to new frame
    figma.viewport.scrollAndZoomIntoView([parentFrame]);

    figma.ui.postMessage({
      type: "done",
      text: `${productCount} slide(s) generated — frame "${newFrameName}"`,
    });
  } catch (err) {
    figma.ui.postMessage({ type: "error", text: err.message });
  }
};
