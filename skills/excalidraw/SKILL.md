---
name: excalidraw
description: >
  Create and manage Excalidraw diagrams in a configured workspace using the
  Excalidraw MCP server. Use this skill whenever the user wants to draw,
  sketch, or diagram anything — architecture diagrams, flowcharts, sequence
  diagrams, network maps, org charts, threat models, or any other visual.
  Triggers: "draw a diagram", "create a flowchart", "sketch the architecture",
  "make an Excalidraw", "visualize this", "diagram the flow", "create a scene",
  "show me in Excalidraw", or any request to produce a visual/diagram/drawing.
  Also use when the user asks to view, edit, search, or organize existing
  Excalidraw scenes or collections.
---

# Excalidraw

> **Beta notice:** The Excalidraw MCP server and its underlying API are
> currently in beta. Tool schemas, parameter names, and response shapes may
> change without notice. If a tool call fails unexpectedly, check whether the
> schema has changed by inspecting the raw error and adjusting accordingly.

Create, view, and manage diagrams through a configured Excalidraw MCP server.

## MCP discovery

This Pi skill uses the `mcp` gateway rather than assuming host-specific direct tool
names. Connect and inspect the live schema before the first operation:

```javascript
mcp({ connect: "excalidraw" })
mcp({ search: "scene", server: "excalidraw" })
mcp({ describe: "<tool path returned by search>" })
```

Call the discovered path with
`mcp({ tool: "<tool path>", args: { ... } })`. Logical tool names below describe
intent; discovery is authoritative if names or arguments change. Use `mcpScript`
when several dependent MCP calls belong in one request.

## Quick Decision

| User wants to…                   | Start here                                    |
| -------------------------------- | --------------------------------------------- |
| Create a new diagram             | [Create a Scene](#create-a-scene)             |
| View or edit an existing diagram | [Find and Edit Scenes](#find-and-edit-scenes) |
| Organize diagrams into a group   | [Collections](#collections)                   |
| Search for a diagram by content  | `search_scene_content`                        |

---

## Create a Scene

Creating a diagram is two steps: make the scene, then add elements.

### Step 1 — Create the scene

```text
create_scene
  name: "My Diagram"
  pinned: false
  collectionId: ""          ← empty string = private; use a real ID for a collection
```

Save the returned `id`.

### Step 2 — Add elements

```text
edit_scene_content
  sceneId: "<id from step 1>"
  add: "<JSON array string — see Element Reference>"
```

The `add` value must be a **JSON-stringified array** of element objects. Do not
include `id` in add payloads — the server assigns them. Use `tempId` to
reference one element from another within the same request (e.g. arrow bindings
pointing at a shape you're also adding).

Always tell the user the scene name and ID when done so they can open it.

---

## Find and Edit Scenes

```text
list_scenes          # all scenes in the workspace
get_scene            # metadata for one scene by ID
get_scene_content    # full element list for a scene
search_scene_content # search by text across all scenes
```

When the user references a diagram without an ID, use `list_scenes` or
`search_scene_content` to find it first.

### Editing elements

`edit_scene_content` is **incremental** — it never replaces the whole scene. Use
it to add, patch, or remove specific elements:

```text
edit_scene_content
  sceneId: "<id>"
  add:    "<JSON array string of new element skeletons>"
  update: "<JSON array string of patches — each must include the real element id>"
  delete: ["<element-id>", ...]
```

To update something: read the scene with `get_scene_content` to get real element
IDs, then send patches via `update`. Only include the properties that should
change — the rest are preserved.

---

## Collections

Collections group related scenes (like folders).

```text
list_collections        # list all collections
get_collection          # details for one collection
list_collection_scenes  # scenes within a collection
create_collection       # create a new collection
create_collection_scene # create a scene inside a collection
update_collection       # rename/update a collection
delete_collection       # delete — confirm with user first
```

To create a scene inside a collection, use `create_collection_scene` (which
handles the association) then push elements with `edit_scene_content` as usual.

---

## Element Reference

All elements are sent as a JSON array — either the `add` value or the `update`
value of `edit_scene_content`.

### Common fields (all types)

```json
{
  "type": "<see types below>",
  "x": 100,
  "y": 100,
  "width": 160,
  "height": 80,
  "backgroundColor": "#a5d8ff",
  "strokeColor": "#1971c2",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "roughness": 1
}
```

`x`/`y` are absolute canvas coordinates. Elements don't share a relative
coordinate space — lay them out explicitly.

### Shape types

| `type`        | Notes                                                                   |
| ------------- | ----------------------------------------------------------------------- |
| `"rectangle"` | Standard box                                                            |
| `"diamond"`   | Decision node in flowcharts                                             |
| `"ellipse"`   | Circle / oval                                                           |
| `"text"`      | Standalone label (no background by default)                             |
| `"arrow"`     | Directed edge — add `points` and optionally `startBinding`/`endBinding` |
| `"line"`      | Non-directional line — add `points`                                     |

### Inline labels on shapes

Attach a text label directly to any shape using the `label` field. This is
simpler than adding a separate `text` element.

```json
{
  "type": "rectangle",
  "x": 100, "y": 100, "width": 160, "height": 80,
  "backgroundColor": "#a5d8ff", "strokeColor": "#1971c2",
  "fillStyle": "solid", "strokeWidth": 2, "roughness": 1,
  "label": {
    "text": "API Gateway",
    "fontSize": 16,
    "fontFamily": 2
  }
}
```

Prefer inline labels over separate `text` elements — they stay attached when the
shape is moved.

### Standalone text element

When you need floating text not tied to a shape:

```json
{
  "type": "text",
  "x": 140, "y": 90,
  "text": "Section Header",
  "fontSize": 20,
  "fontFamily": 2,
  "textAlign": "center",
  "strokeColor": "#1e1e1e",
  "backgroundColor": "transparent"
}
```

`fontFamily`: 1 = Excalidraw (handwritten), 2 = Nunito (normal), 3 = Cascadia
Code (monospace)

### Arrow element

```json
{
  "type": "arrow",
  "x": 262, "y": 140,
  "points": [[0, 0], [116, 0]],
  "strokeColor": "#1e1e1e",
  "strokeWidth": 2,
  "roughness": 1,
  "startArrowhead": null,
  "endArrowhead": "arrow",
  "startBinding": {
    "elementId": "rect-a",
    "focus": 0,
    "gap": 2,
    "type": "inside"
  },
  "endBinding": {
    "elementId": "rect-b",
    "focus": 0,
    "gap": 2,
    "type": "inside"
  }
}
```

When adding an arrow that connects shapes **in the same request**, use `tempId`
on the shapes and reference those `tempId` values in the arrow's
`startBinding.elementId` / `endBinding.elementId`. The server resolves them to
real IDs before saving.

`x`/`y` of the arrow is the starting point; `points` are relative offsets from
there. For a horizontal arrow going right 116px: `points: [[0,0],[116,0]]`.

### Visual Vocabulary

Use shape, fill, and color together to encode element type. A viewer should be
able to identify what a node is at a glance — before reading its label.

**Apply these consistently across every diagram:**

| Element type         | Shape       | `fillStyle`     | `backgroundColor` | `strokeColor` | `strokeWidth` |
| -------------------- | ----------- | --------------- | ----------------- | ------------- | ------------- |
| Client / User        | `ellipse`   | `"solid"`       | `"#d0bfff"`       | `"#6741d9"`   | 2             |
| API Gateway          | `rectangle` | `"solid"`       | `"#a5d8ff"`       | `"#1971c2"`   | 2             |
| Microservice         | `rectangle` | `"solid"`       | `"#b2f2bb"`       | `"#2f9e44"`   | 2             |
| Message topic /queue | `rectangle` | `"hachure"`     | `"#ffec99"`       | `"#e67700"`   | 2             |
| Database / KV store  | `rectangle` | `"cross-hatch"` | `"#f1f3f5"`       | `"#868e96"`   | 1             |
| Cache (Redis…)       | `rectangle` | `"dots"`        | `"#ffe8cc"`       | `"#fd7e14"`   | 1             |
| External service     | `rectangle` | `"zigzag"`      | `"#f8f9fa"`       | `"#495057"`   | 2             |
| Critical service     | `rectangle` | `"solid"`       | `"#ffc9c9"`       | `"#c92a2a"`   | 2             |
| Worker / consumer    | `rectangle` | `"hachure"`     | `"#d0bfff"`       | `"#6741d9"`   | 2             |
| Decision             | `diamond`   | `"solid"`       | `"#ffec99"`       | `"#e67700"`   | 2             |
| Cluster boundary     | `rectangle` | `"hachure"`     | `"transparent"`   | (group color) | 2, `"dashed"` |

Every diagram must include a **legend** (see [Legends](#legends) below).

### Arrow Protocols

Label every arrow with the technology or protocol it uses. Don't write generic
"publish" or "subscribe" — write the actual transport so the diagram is
self-documenting.

| Protocol / transport  | `strokeColor` | `strokeWidth` | `strokeStyle` | Label example        |
| --------------------- | ------------- | ------------- | ------------- | -------------------- |
| HTTP / REST           | `"#1e1e1e"`   | 2             | `"solid"`     | `"REST"`             |
| gRPC                  | `"#2f9e44"`   | 2             | `"solid"`     | `"gRPC"`             |
| Kafka (publish)       | `"#e67700"`   | 2             | `"solid"`     | `"Kafka"`            |
| Kafka (subscribe)     | `"#e67700"`   | 1             | `"dashed"`    | `"Kafka"`            |
| AMQP / RabbitMQ       | `"#f76707"`   | 2             | `"solid"`     | `"AMQP"`             |
| SQL                   | `"#868e96"`   | 1             | `"solid"`     | `"SQL"`              |
| Redis protocol        | `"#fd7e14"`   | 1             | `"solid"`     | `"Redis"`            |
| WebSocket             | `"#1971c2"`   | 2             | `"dashed"`    | `"WS"`               |
| Async / notification  | `"#6741d9"`   | 1             | `"dashed"`    | `"push"` / `"async"` |
| Internal / in-process | `"#868e96"`   | 1             | `"dashed"`    | (no label needed)    |

---

## Layout Tips

### General principles

- Space nodes ~60–80px apart for readable diagrams
- A typical service box: 160×80px
- A typical decision diamond: 140×80px
- **Establish one primary flow direction and never break it.** If the main flow
  is left-to-right, every arrow in the primary path must go left-to-right.
  Crossing arrows — even one — make a diagram hard to follow.
- Arrows should only go "backwards" (against the primary direction) if they are
  visually distinct (dashed, thin, different color) and clearly labeled. Limit
  these to at most one or two per diagram.

### Choosing a layout pattern

Pick the pattern that matches the diagram type before placing any nodes:

| Diagram type                                         | Pattern                                                    | Primary flow |
| ---------------------------------------------------- | ---------------------------------------------------------- | ------------ |
| Simple request/response, pipeline                    | **Linear** — all nodes in a row                            | Left → Right |
| Fan-out from a single source                         | **Hub-and-spoke** — hub at top, consumers below            | Top → Down   |
| Sequential saga / event chain                        | **Linear** — services and topics alternate in a single row | Left → Right |
| Hierarchical system (load balancer → services → DBs) | **Tree** — root at top, children below                     | Top → Down   |
| Flowchart with decisions                             | **Vertical flowchart** — start top, branch down            | Top → Down   |

### Saga / event-driven layouts

The most common mistake is placing an event bus as a central hub with publishers
above and consumers below, then adding feedback arrows that go upward. This
creates a tangle.

Instead, **model each saga step as a left-to-right waypoint**:

```text
[Service A] → [topic.x] → [Service B] → [topic.y] → [Service C]
```

- Topic boxes sit between the services that produce and consume them
- Databases hang directly below their service (short downward arrow)
- Cross-cutting consumers (e.g. Notification Service) sit below the row and
  receive short downward arrows from the relevant topics
- Wrap a dashed `strokeStyle: "dashed"` boundary box around all topic boxes to
  indicate they live inside the same broker

### Sizing reference

- Service/consumer box: 130–160 × 70–80px
- Topic/queue box: 120–140 × 60–70px (slightly shorter than service boxes)
- Database/cache box: 110–130 × 40–50px (shorter, thinner stroke)
- Decision diamond: 140×80px
- Group/cluster boundary: `strokeStyle: "dashed"`,
  `backgroundColor:
  "transparent"`, colored stroke matching the contained
  elements
- Legend box: 160–200px wide, placed bottom-left, clear of the main diagram

### Legends

Every diagram must include a legend so the visual vocabulary is self-explaining.
Place it in the **bottom-left corner**, separated from the main diagram by at
least 40px.

Build the legend as a group of small shapes + text:

1. **Background box** — `rectangle`, `fillStyle: "solid"`,
   `backgroundColor: "#f8f9fa"`, `strokeColor: "#dee2e6"`, `strokeWidth: 1`,
   sized to fit contents.
2. **"Legend" heading** — `text` element, `fontSize: 13`, positioned at the top
   of the box.
3. **One row per element type used** — a miniature shape (40×22px) with the
   exact `fillStyle`, `backgroundColor`, and `strokeColor` of the real element,
   plus a `text` label to its right (e.g. "Microservice", "Kafka Topic",
   "Database"). Row height: ~30px. Left-pad shapes 10px inside the box.
4. **One row per arrow protocol used** — a short `arrow` element (40px wide,
   matching `strokeColor`/`strokeStyle`/`strokeWidth`) with a text label to its
   right.

Only include types and protocols that actually appear in the diagram.

---

## Full Example: Two-Service Flow

```json
[
  {
    "type": "rectangle",
    "x": 100, "y": 100, "width": 160, "height": 80,
    "backgroundColor": "#a5d8ff", "strokeColor": "#1971c2",
    "fillStyle": "solid", "strokeWidth": 2, "roughness": 1,
    "label": {"text": "Service A", "fontSize": 16, "fontFamily": 2},
    "tempId": "rect-a"
  },
  {
    "type": "rectangle",
    "x": 380, "y": 100, "width": 160, "height": 80,
    "backgroundColor": "#b2f2bb", "strokeColor": "#2f9e44",
    "fillStyle": "solid", "strokeWidth": 2, "roughness": 1,
    "label": {"text": "Service B", "fontSize": 16, "fontFamily": 2},
    "tempId": "rect-b"
  },
  {
    "type": "arrow",
    "x": 262, "y": 140, "points": [[0, 0], [116, 0]],
    "strokeColor": "#1e1e1e", "strokeWidth": 2, "roughness": 1,
    "startArrowhead": null, "endArrowhead": "arrow",
    "startBinding": {"elementId": "rect-a", "focus": 0, "gap": 2, "type": "inside"},
    "endBinding":   {"elementId": "rect-b", "focus": 0, "gap": 2, "type": "inside"}
  }
]
```

Pass this array JSON-stringified as the `add` parameter of `edit_scene_content`.

---

## Self-Check

Run both phases before reporting the diagram as done.

### Before adding elements

Settle these before the first `edit_scene_content` call:

1. **Layout pattern** — choose one from the
   [pattern table](#choosing-a-layout-pattern); all coordinates follow from this
   choice
2. **Element inventory** — every node maps to a row in the Visual Vocabulary
   table; no ad-hoc colors or fill styles
3. **Arrow protocols** — every connection has a named protocol; no unlabeled
   arrows
4. **Legend position** — bottom-left corner, ≥40px below the lowest element in
   the main diagram

### Before reporting done

Work through this list. Fix any failure with `edit_scene_content` (read real IDs
first with `get_scene_content` if needed), then re-check.

| Check               | Pass condition                                                                                     |
| ------------------- | -------------------------------------------------------------------------------------------------- |
| **Flow direction**  | Primary flow is consistent; no main-path arrow runs backwards against it                           |
| **Saga layout**     | Event-driven flows use left-to-right waypoints, not a central hub                                  |
| **Visual vocab**    | Every element type matches the exact shape, `fillStyle`, and color in the Visual Vocabulary table  |
| **Visual distinct** | Different element types look distinct at a glance — no two share shape + fill + color              |
| **Arrow labels**    | Every arrow has a protocol label (`"REST"`, `"Kafka"`, `"SQL"`, `"gRPC"`, `"Redis"`, `"WS"`, etc.) |
| **Kafka encoding**  | Publish: solid, `strokeWidth: 2`; subscribe: dashed, `strokeWidth: 1`                              |
| **Legend**          | Present in the bottom-left; one row per element type used, one row per protocol used               |

---

## After Creating or Editing

Keep the response concise — the user cares that it worked and where to find it,
not the implementation details. One or two sentences is enough:

> Created **"API Gateway Architecture"** (`8mZkd44rtls`) — load balancer at the
> top fanning down through the API gateway to three color-coded services, each
> with its own Postgres database.

Don't reproduce element lists, coordinate tables, or JSON payloads in the
response. If the user wants to tweak something, they'll ask.
