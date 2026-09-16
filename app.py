import json
import html

import streamlit as st
import streamlit.components.v1 as components

from modules.risk_engine import calculate_risk
from modules.transaction_intelligence import analyze_transactions


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="CryptoShield | Blockchain Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# TRANSACTION HELPERS
# =========================================================

def get_sender(tx):
    """Return sender address from common transaction formats."""

    if not isinstance(tx, dict):
        return ""

    for key in [
        "from",
        "from_address",
        "sender",
        "source",
    ]:
        value = tx.get(key)

        if value:
            return str(value)

    return ""


def get_receiver(tx):
    """Return receiver address from common transaction formats."""

    if not isinstance(tx, dict):
        return ""

    for key in [
        "to",
        "to_address",
        "receiver",
        "destination",
    ]:
        value = tx.get(key)

        if value:
            return str(value)

    return ""


def get_transaction_value(tx):
    """Return transaction value from common formats."""

    if not isinstance(tx, dict):
        return 0

    for key in [
        "value",
        "amount",
        "value_eth",
        "amount_eth",
        "value_native",
    ]:
        if tx.get(key) is not None:
            return tx.get(key)

    return 0


def get_transaction_hash(tx):
    """Return transaction hash."""

    if not isinstance(tx, dict):
        return "N/A"

    for key in [
        "hash",
        "tx_hash",
        "transaction_hash",
    ]:
        value = tx.get(key)

        if value:
            return str(value)

    return "N/A"


def short_address(address):
    """Shorten long blockchain addresses."""

    address = str(address or "")

    if len(address) > 18:
        return address[:10] + "..." + address[-8:]

    return address


# =========================================================
# FUND FLOW GRAPH
# =========================================================

def build_premium_graph(transactions, wallet_address):

    wallet_address = str(wallet_address or "").strip()

    nodes = {}
    edges = []

    # -----------------------------------------------------
    # Add suspect wallet
    # -----------------------------------------------------

    if wallet_address:

        nodes[wallet_address.lower()] = {
            "id": wallet_address,
            "label": "SUSPECT WALLET",
            "title": (
                "<b>Suspect Wallet</b><br>"
                + html.escape(wallet_address)
            ),
            "group": "suspect",
        }

    # -----------------------------------------------------
    # Process transactions
    # -----------------------------------------------------

    valid_transaction_count = 0

    for index, tx in enumerate(transactions or []):

        if not isinstance(tx, dict):
            continue

        sender = get_sender(tx)
        receiver = get_receiver(tx)

        if not sender or not receiver:
            continue

        valid_transaction_count += 1

        sender_key = sender.lower()
        receiver_key = receiver.lower()

        # -------------------------------------------------
        # Sender node
        # -------------------------------------------------

        if sender_key not in nodes:

            nodes[sender_key] = {
                "id": sender,
                "label": short_address(sender),
                "title": (
                    "<b>Wallet</b><br>"
                    + html.escape(sender)
                ),
                "group": "wallet",
            }

        # -------------------------------------------------
        # Receiver node
        # -------------------------------------------------

        if receiver_key not in nodes:

            nodes[receiver_key] = {
                "id": receiver,
                "label": short_address(receiver),
                "title": (
                    "<b>Wallet</b><br>"
                    + html.escape(receiver)
                ),
                "group": "wallet",
            }

        # -------------------------------------------------
        # Transaction value
        # -------------------------------------------------

        amount = get_transaction_value(tx)

        try:
            amount_display = f"{float(amount):,.4f}"
        except (TypeError, ValueError):
            amount_display = str(amount)

        tx_hash = get_transaction_hash(tx)

        # -------------------------------------------------
        # Edge
        # -------------------------------------------------

        edges.append(
            {
                "id": f"edge-{index}",
                "from": sender,
                "to": receiver,
                "arrows": "to",
                "label": amount_display,
                "title": (
                    "<b>Transaction</b><br>"
                    f"Amount: {html.escape(amount_display)}<br>"
                    f"Hash: {html.escape(tx_hash)}"
                ),
            }
        )

    # -----------------------------------------------------
    # JSON
    # -----------------------------------------------------

    nodes_json = json.dumps(list(nodes.values()))
    edges_json = json.dumps(edges)
    wallet_json = json.dumps(wallet_address)

    # -----------------------------------------------------
    # Graph HTML
    # -----------------------------------------------------

    graph_html = """
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<script
src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js">
</script>

<style>

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    padding: 0;

    width: 100%;
    height: 100%;

    overflow: hidden;

    background: #050914;

    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

#graph-wrapper {

    position: relative;

    width: 100%;

    height: 720px;

    overflow: hidden;

    border-radius: 22px;

    border:
        1px solid rgba(148, 163, 184, 0.16);

    background:
        radial-gradient(
            circle at 50% 45%,
            rgba(37, 99, 235, 0.14),
            transparent 34%
        ),
        radial-gradient(
            circle at 15% 20%,
            rgba(124, 58, 237, 0.10),
            transparent 28%
        ),
        #050914;

    box-shadow:
        inset 0 0 100px rgba(37, 99, 235, 0.035),
        0 25px 80px rgba(0, 0, 0, 0.40);
}

#graph {

    width: 100%;

    height: 100%;
}

.grid {

    position: absolute;

    inset: 0;

    pointer-events: none;

    opacity: 0.16;

    background-image:
        linear-gradient(
            rgba(96, 165, 250, 0.07) 1px,
            transparent 1px
        ),
        linear-gradient(
            90deg,
            rgba(96, 165, 250, 0.07) 1px,
            transparent 1px
        );

    background-size: 42px 42px;
}

.topbar {

    position: absolute;

    top: 16px;
    left: 18px;
    right: 18px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    pointer-events: none;

    z-index: 10;
}

.graph-title {

    padding: 11px 15px;

    border-radius: 13px;

    background:
        rgba(8, 13, 24, 0.86);

    border:
        1px solid rgba(148, 163, 184, 0.14);

    backdrop-filter: blur(16px);

    color: #e2e8f0;

    font-size: 13px;

    font-weight: 800;

    letter-spacing: 0.04em;
}

.graph-subtitle {

    margin-top: 3px;

    color: #64748b;

    font-size: 9px;

    font-weight: 700;

    letter-spacing: 0.08em;

    text-transform: uppercase;
}

.legend {

    display: flex;

    gap: 10px;

    padding: 10px 13px;

    border-radius: 13px;

    background:
        rgba(8, 13, 24, 0.86);

    border:
        1px solid rgba(148, 163, 184, 0.14);

    backdrop-filter: blur(16px);
}

.legend-item {

    display: flex;

    align-items: center;

    gap: 6px;

    color: #94a3b8;

    font-size: 10px;

    font-weight: 700;
}

.dot {

    width: 8px;
    height: 8px;

    border-radius: 50%;
}

.dot-suspect {

    background: #ef4444;

    box-shadow:
        0 0 13px rgba(239, 68, 68, 0.9);
}

.dot-wallet {

    background: #3b82f6;

    box-shadow:
        0 0 12px rgba(59, 130, 246, 0.8);
}

.controls {

    position: absolute;

    left: 18px;
    bottom: 18px;

    display: flex;

    gap: 7px;

    z-index: 10;
}

.control {

    pointer-events: auto;

    border:
        1px solid rgba(148, 163, 184, 0.16);

    background:
        rgba(8, 13, 24, 0.90);

    color: #cbd5e1;

    border-radius: 10px;

    padding: 8px 11px;

    cursor: pointer;

    font-size: 10px;

    font-weight: 800;

    backdrop-filter: blur(14px);
}

.control:hover {

    background:
        rgba(37, 99, 235, 0.30);

    border-color:
        rgba(96, 165, 250, 0.50);

    color: white;
}

.wallet-badge {

    position: absolute;

    right: 18px;
    bottom: 18px;

    z-index: 10;

    max-width: 260px;

    padding: 10px 13px;

    border-radius: 11px;

    background:
        rgba(8, 13, 24, 0.90);

    border:
        1px solid rgba(239, 68, 68, 0.22);

    color: #94a3b8;

    font-size: 10px;

    backdrop-filter: blur(14px);
}

.wallet-badge strong {

    display: block;

    color: #f87171;

    font-size: 9px;

    letter-spacing: 0.09em;

    text-transform: uppercase;

    margin-bottom: 3px;
}

.empty-message {

    position: absolute;

    top: 50%;
    left: 50%;

    transform: translate(-50%, -50%);

    text-align: center;

    color: #64748b;

    z-index: 5;
}

.empty-message strong {

    display: block;

    color: #94a3b8;

    font-size: 15px;

    margin-bottom: 8px;
}

</style>

</head>

<body>

<div id="graph-wrapper">

    <div class="grid"></div>

    <div class="topbar">

        <div class="graph-title">

            🕸️ FUND FLOW INTELLIGENCE

            <div class="graph-subtitle">
                Interactive transaction topology
            </div>

        </div>

        <div class="legend">

            <div class="legend-item">

                <span class="dot dot-suspect"></span>

                Suspect

            </div>

            <div class="legend-item">

                <span class="dot dot-wallet"></span>

                Wallet

            </div>

        </div>

    </div>

    <div id="graph"></div>

    <div class="controls">

        <button
            class="control"
            onclick="network.fit({animation:true})"
        >
            ⛶ FIT
        </button>

        <button
            class="control"
            onclick="focusSuspect()"
        >
            ◎ SUSPECT
        </button>

        <button
            class="control"
            onclick="zoomOut()"
        >
            − ZOOM
        </button>

        <button
            class="control"
            onclick="zoomIn()"
        >
            + ZOOM
        </button>

    </div>

    <div class="wallet-badge">

        <strong>Target Wallet</strong>

        WALLET_PLACEHOLDER

    </div>

</div>

<script>

const nodeData = NODE_DATA_PLACEHOLDER;

const edgeData = EDGE_DATA_PLACEHOLDER;

const targetWallet = WALLET_JSON_PLACEHOLDER;


const nodes = new vis.DataSet(nodeData);

const edges = new vis.DataSet(edgeData);


const container =
    document.getElementById("graph");


const data = {
    nodes: nodes,
    edges: edges
};


const options = {

    autoResize: true,

    interaction: {

        hover: true,

        tooltipDelay: 120,

        navigationButtons: false,

        keyboard: true,

        zoomView: true,

        dragView: true,

        dragNodes: true
    },

    physics: {

        enabled: true,

        solver: "forceAtlas2Based",

        forceAtlas2Based: {

            gravitationalConstant: -125,

            centralGravity: 0.008,

            springLength: 185,

            springConstant: 0.035,

            damping: 0.82,

            avoidOverlap: 1.2
        },

        stabilization: {

            enabled: true,

            iterations: 250,

            updateInterval: 25,

            fit: true
        }
    },

    nodes: {

        shape: "dot",

        size: 15,

        borderWidth: 2,

        shadow: {

            enabled: true,

            color: "rgba(59,130,246,0.45)",

            size: 18,

            x: 0,

            y: 0
        },

        font: {

            color: "#cbd5e1",

            size: 12,

            face: "Inter, sans-serif",

            strokeWidth: 3,

            strokeColor: "#050914"
        }
    },

    groups: {

        suspect: {

            color: {

                background: "#ef4444",

                border: "#fecaca",

                highlight: {

                    background: "#f87171",

                    border: "#ffffff"
                }
            },

            size: 29,

            borderWidth: 3,

            shadow: {

                enabled: true,

                color: "rgba(239,68,68,0.85)",

                size: 28,

                x: 0,

                y: 0
            },

            font: {

                color: "#fee2e2",

                size: 13,

                bold: true,

                strokeWidth: 4,

                strokeColor: "#050914"
            }
        },

        wallet: {

            color: {

                background: "#2563eb",

                border: "#60a5fa",

                highlight: {

                    background: "#3b82f6",

                    border: "#bfdbfe"
                }
            }
        }
    },

    edges: {

        arrows: {

            to: {

                enabled: true,

                scaleFactor: 0.65
            }
        },

        color: {

            color: "rgba(96,165,250,0.32)",

            highlight: "#60a5fa",

            hover: "#93c5fd",

            inherit: false
        },

        width: 1.5,

        selectionWidth: 3,

        smooth: {

            enabled: true,

            type: "dynamic",

            roundness: 0.25
        },

        font: {

            color: "#64748b",

            size: 9,

            strokeWidth: 3,

            strokeColor: "#050914",

            align: "middle"
        }
    },

    layout: {

        improvedLayout: true
    }
};


const network = new vis.Network(
    container,
    data,
    options
);


// =====================================================
// FOCUS SUSPECT
// =====================================================

function focusSuspect() {

    if (!targetWallet) {

        network.fit({
            animation: true
        });

        return;
    }

    network.focus(
        targetWallet,
        {
            scale: 1.15,

            animation: {

                duration: 800,

                easingFunction: "easeInOutQuad"
            }
        }
    );
}


// =====================================================
// ZOOM
// =====================================================

function zoomIn() {

    network.moveTo({
        scale: network.getScale() * 1.2,
        animation: true
    });
}


function zoomOut() {

    network.moveTo({
        scale: network.getScale() * 0.8,
        animation: true
    });
}


// =====================================================
// HOVER
// =====================================================

network.on(
    "hoverNode",
    function() {

        document.body.style.cursor =
            "pointer";
    }
);


network.on(
    "blurNode",
    function() {

        document.body.style.cursor =
            "default";
    }
);


// =====================================================
// NODE SELECTION
// =====================================================

network.on(
    "selectNode",
    function(params) {

        const selected =
            params.nodes[0];

        if (!selected) {
            return;
        }

        const connectedNodes =
            network.getConnectedNodes(
                selected
            );

        const connectedEdges =
            network.getConnectedEdges(
                selected
            );


        const nodeUpdates = [];


        nodes.forEach(
            function(node) {

                if (
                    node.id === selected ||
                    connectedNodes.includes(node.id)
                ) {

                    nodeUpdates.push({
                        id: node.id,
                        opacity: 1
                    });

                } else {

                    nodeUpdates.push({
                        id: node.id,
                        opacity: 0.18
                    });
                }
            }
        );


        nodes.update(nodeUpdates);


        const edgeUpdates = [];


        edges.forEach(
            function(edge) {

                if (
                    connectedEdges.includes(edge.id)
                ) {

                    edgeUpdates.push({

                        id: edge.id,

                        color: {
                            color: "#60a5fa"
                        },

                        width: 3
                    });

                } else {

                    edgeUpdates.push({

                        id: edge.id,

                        color: {
                            color:
                                "rgba(96,165,250,0.08)"
                        },

                        width: 1
                    });
                }
            }
        );


        edges.update(edgeUpdates);
    }
);


// =====================================================
// RESET
// =====================================================

network.on(
    "click",
    function(params) {

        if (params.nodes.length !== 0) {
            return;
        }


        const nodeUpdates = [];


        nodes.forEach(
            function(node) {

                nodeUpdates.push({

                    id: node.id,

                    opacity: 1
                });
            }
        );


        nodes.update(nodeUpdates);


        const edgeUpdates = [];


        edges.forEach(
            function(edge) {

                edgeUpdates.push({

                    id: edge.id,

                    color: {
                        color:
                            "rgba(96,165,250,0.32)"
                    },

                    width: 1.5
                });
            }
        );


        edges.update(edgeUpdates);
    }
);


// =====================================================
// INITIAL FIT
// =====================================================

network.once(
    "stabilizationIterationsDone",
    function() {

        network.fit({

            animation: {

                duration: 900,

                easingFunction:
                    "easeInOutQuad"
            }
        });
    }
);

</script>

</body>

</html>
"""

    # -----------------------------------------------------
    # Replace placeholders safely
    # -----------------------------------------------------

    graph_html = graph_html.replace(
        "NODE_DATA_PLACEHOLDER",
        nodes_json
    )

    graph_html = graph_html.replace(
        "EDGE_DATA_PLACEHOLDER",
        edges_json
    )

    graph_html = graph_html.replace(
        "WALLET_JSON_PLACEHOLDER",
        wallet_json
    )

    graph_html = graph_html.replace(
        "WALLET_PLACEHOLDER",
        html.escape(short_address(wallet_address))
    )

    return graph_html, valid_transaction_count


# =========================================================
# GLOBAL CSS
# =========================================================

st.markdown(
    """
<style>

.stApp {

    background:
        radial-gradient(
            circle at 10% 5%,
            rgba(37, 99, 235, 0.12),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(124, 58, 237, 0.10),
            transparent 25%
        ),
        #060a12;

    color: #e5e7eb;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    background: transparent !important;
}

.block-container {

    max-width: 1450px;

    padding-top: 2rem;

    padding-bottom: 3rem;
}

[data-testid="stSidebar"] {

    background: #080d18;

    border-right:
        1px solid rgba(148, 163, 184, 0.12);
}

.brand {

    font-size: 1.55rem;

    font-weight: 800;

    color: #f8fafc;

    letter-spacing: -0.03em;
}

.brand-blue {
    color: #60a5fa;
}

.subtitle {

    color: #64748b;

    font-size: 0.78rem;

    margin-top: 4px;
}

.side-section {

    color: #64748b;

    font-size: 0.68rem;

    font-weight: 800;

    letter-spacing: 0.10em;

    text-transform: uppercase;

    margin-top: 1.6rem;

    margin-bottom: 0.55rem;
}

.side-item {

    color: #94a3b8;

    padding: 0.65rem 0.75rem;

    border-radius: 9px;

    font-size: 0.86rem;

    margin-bottom: 2px;
}

.status {

    display: flex;

    align-items: center;

    gap: 8px;

    color: #94a3b8;

    font-size: 0.76rem;
}

.status-dot {

    width: 8px;

    height: 8px;

    border-radius: 50%;

    background: #22c55e;

    box-shadow:
        0 0 12px
        rgba(34, 197, 94, 0.75);
}

.hero {

    padding: 2.7rem 2.8rem;

    border-radius: 22px;

    border:
        1px solid rgba(148, 163, 184, 0.13);

    background:
        linear-gradient(
            135deg,
            rgba(15, 23, 42, 0.92),
            rgba(15, 23, 42, 0.60)
        );

    box-shadow:
        0 25px 70px rgba(0, 0, 0, 0.35);

    margin-bottom: 1.5rem;
}

.hero-label {

    display: inline-block;

    padding: 0.38rem 0.8rem;

    border-radius: 999px;

    background:
        rgba(37, 99, 235, 0.13);

    border:
        1px solid rgba(96, 165, 250, 0.22);

    color: #93c5fd;

    font-size: 0.70rem;

    font-weight: 800;

    letter-spacing: 0.08em;
}

.hero-title {

    font-size: 2.75rem;

    line-height: 1.08;

    margin-top: 1rem;

    margin-bottom: 0.8rem;

    color: #f8fafc;

    letter-spacing: -0.045em;

    font-weight: 850;
}

.hero-text {

    color: #94a3b8;

    font-size: 1rem;

    max-width: 780px;

    line-height: 1.75;
}

.panel {

    padding: 1.45rem;

    border-radius: 18px;

    border:
        1px solid rgba(148, 163, 184, 0.13);

    background:
        rgba(15, 23, 42, 0.65);

    margin-bottom: 1rem;
}

.panel-title {

    color: #f8fafc;

    font-size: 1.05rem;

    font-weight: 800;

    margin-bottom: 0.3rem;
}

.panel-description {

    color: #64748b;

    font-size: 0.82rem;

    line-height: 1.5;
}

.stTextInput input {

    background: #0b1220 !important;

    color: #e5e7eb !important;

    border-radius: 12px !important;

    border:
        1px solid
        rgba(148, 163, 184, 0.16)
        !important;
}

div[data-baseweb="select"] > div {

    background: #0b1220 !important;

    border-radius: 12px !important;

    border:
        1px solid
        rgba(148, 163, 184, 0.16)
        !important;
}

.stButton > button {

    width: 100%;

    min-height: 46px;

    border-radius: 12px;

    border:
        1px solid
        rgba(96, 165, 250, 0.28);

    background:
        linear-gradient(
            135deg,
            #2563eb,
            #4f46e5
        );

    color: white;

    font-weight: 800;
}

.metric-card {

    padding: 1.25rem;

    min-height: 100px;

    border-radius: 16px;

    border:
        1px solid
        rgba(148, 163, 184, 0.12);

    background:
        linear-gradient(
            145deg,
            rgba(15, 23, 42, 0.80),
            rgba(15, 23, 42, 0.50)
        );
}

.metric-label {

    color: #64748b;

    font-size: 0.68rem;

    text-transform: uppercase;

    letter-spacing: 0.08em;

    font-weight: 700;
}

.metric-value {

    color: #f8fafc;

    font-size: 1.55rem;

    font-weight: 850;

    margin-top: 0.35rem;
}

.footer {

    text-align: center;

    color: #475569;

    font-size: 0.70rem;

    margin-top: 2.5rem;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.html(
        """
        <div class="brand">
            🛡️ Crypto<span class="brand-blue">Shield</span>
        </div>

        <div class="subtitle">
            Blockchain Intelligence Platform
        </div>
        """
    )

    st.html(
        """
        <div class="side-section">
            Investigation
        </div>

        <div class="side-item">
            ◉ New Investigation
        </div>

        <div class="side-item">
            ⌕ Investigation History
        </div>

        <div class="side-item">
            ◈ Intelligence
        </div>

        <div class="side-section">
            System
        </div>

        <div class="side-item">
            ⚙ Configuration
        </div>

        <div class="side-item">
            ◌ System Status
        </div>
        """
    )

    st.markdown("---")

    st.html(
        """
        <div class="status">

            <div class="status-dot"></div>

            <span>
                Core systems online
            </span>

        </div>
        """
    )


# =========================================================
# HERO
# =========================================================

st.html(
    """
    <div class="hero">

        <div class="hero-label">
            SIH 26183 · INVESTIGATION CONSOLE
        </div>

        <div class="hero-title">
            Real-Time Crypto Fraud Intelligence
        </div>

        <div class="hero-text">
            Transform a victim-reported cryptocurrency
            wallet address into an evidence-driven
            blockchain investigation. Trace transaction
            flows, identify suspicious patterns, and build
            actionable intelligence for investigators.
        </div>

    </div>
    """
)


# =========================================================
# INVESTIGATION INTAKE
# =========================================================

st.html(
    """
    <div class="panel">

        <div class="panel-title">
            🔎 Start New Investigation
        </div>

        <div class="panel-description">
            Enter the suspect wallet reported by the victim.
            Blockchain analysis will begin after submission.
        </div>

    </div>
    """
)


# =========================================================
# INPUT
# =========================================================

col1, col2 = st.columns([3, 1])


with col1:

    wallet_address = st.text_input(
        "Suspect wallet address",
        placeholder="Enter Ethereum wallet address...",
    )


with col2:

    blockchain = st.selectbox(
        "Blockchain",
        [
            "Ethereum",
            "BNB Chain",
            "Polygon",
            "Arbitrum",
            "Base",
            "Optimism",
        ],
    )


# =========================================================
# START INVESTIGATION
# =========================================================

if st.button("🚀 Start Investigation"):

    if not wallet_address.strip():

        st.warning(
            "Please enter a wallet address to begin "
            "the investigation."
        )

    else:

        try:

            from modules.investigation import investigate_wallet

            with st.spinner(
                f"Analyzing {blockchain} blockchain transactions..."
            ):

                investigation_result = investigate_wallet(
                    wallet_address.strip()
                )

            st.session_state[
                "investigation_result"
            ] = investigation_result

            st.success(
                "Blockchain investigation completed successfully."
            )

        except Exception as e:

            st.error(
                f"Investigation failed: {e}"
            )


# =========================================================
# RESULTS
# =========================================================

if "investigation_result" in st.session_state:

    result = st.session_state[
        "investigation_result"
    ]

    if not isinstance(result, dict):

        st.error(
            "Investigation returned an unexpected "
            "result format."
        )

    else:

        # -------------------------------------------------
        # Get data FIRST
        # -------------------------------------------------

        analysis = result.get(
            "analysis",
            {}
        )

        transactions = result.get(
            "transactions",
            []
        )

        target_wallet = result.get(
            "wallet_address",
            wallet_address.strip()
        )

        if not isinstance(transactions, list):

            transactions = []

        # -------------------------------------------------
        # Transaction intelligence
        # -------------------------------------------------

        intelligence = analyze_transactions(
            transactions,
            target_wallet
        )

        # -------------------------------------------------
        # Metrics
        # -------------------------------------------------

        st.markdown(
            "### 🔎 Investigation Results"
        )

        r1, r2, r3, r4 = st.columns(4)

        with r1:

            st.metric(
                "Transactions",
                analysis.get(
                    "total_transactions",
                    len(transactions)
                ),
            )

        with r2:

            st.metric(
                "Incoming",
                analysis.get(
                    "incoming_transactions",
                    0
                ),
            )

        with r3:

            st.metric(
                "Outgoing",
                analysis.get(
                    "outgoing_transactions",
                    0
                ),
            )

        with r4:

            st.metric(
                "Counterparties",
                analysis.get(
                    "unique_counterparties",
                    intelligence.get(
                        "unique_counterparties",
                        0
                    )
                ),
            )

        # =================================================
        # RISK INTELLIGENCE
        # =================================================

        st.markdown("### 🛡️ Risk Intelligence")

        try:

            risk_result = calculate_risk(
                transactions
            )

            risk_score = risk_result.get(
                "score",
                0
            )

            risk_level = risk_result.get(
                "level",
                "UNKNOWN"
            )

            risk_reasons = risk_result.get(
                "reasons",
                []
            )

        except Exception as risk_error:

            risk_score = 0
            risk_level = "UNAVAILABLE"
            risk_reasons = [
                f"Risk engine error: {risk_error}"
            ]

        st.html(
            f"""
            <div style="
                padding:1.5rem;
                border-radius:18px;
                border:1px solid rgba(239,68,68,0.20);
                background:
                    linear-gradient(
                        135deg,
                        rgba(127,29,29,0.18),
                        rgba(15,23,42,0.75)
                    );
            ">

                <div style="
                    display:flex;
                    align-items:center;
                    gap:30px;
                    flex-wrap:wrap;
                ">

                    <div>

                        <div style="
                            color:#f87171;
                            font-size:2rem;
                            font-weight:900;
                        ">
                            {risk_score}/100
                        </div>

                        <div style="
                            color:#fca5a5;
                            font-size:0.75rem;
                            font-weight:800;
                            letter-spacing:0.08em;
                        ">
                            {html.escape(str(risk_level))}
                        </div>

                    </div>

                    <div style="
                        flex:1;
                        min-width:250px;
                    ">

                        <div style="
                            color:#94a3b8;
                            font-size:0.75rem;
                            font-weight:700;
                            margin-bottom:8px;
                        ">
                            DETECTED INDICATORS
                        </div>

                        {
                            "".join(
                                f'''
                                <div style="
                                    color:#cbd5e1;
                                    font-size:0.82rem;
                                    margin:6px 0;
                                ">
                                    ⚠ {html.escape(str(reason))}
                                </div>
                                '''
                                for reason in risk_reasons
                            )
                            if risk_reasons
                            else
                            '<div style="color:#64748b;">No indicators reported.</div>'
                        }

                    </div>

                </div>

            </div>
            """
        )

        # =================================================
        # TRANSACTION INTELLIGENCE
        # =================================================

        st.markdown("---")

        st.subheader(
            "🧠 Transaction Intelligence"
        )

        st.caption(
            "Automated analysis of transaction behavior "
            "and recurring patterns."
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Transactions Analyzed",
                intelligence.get(
                    "transactions_analyzed",
                    0
                )
            )

        with col2:

            st.metric(
                "Flagged Transactions",
                intelligence.get(
                    "suspicious_transactions",
                    0
                )
            )

        with col3:

            st.metric(
                "Unique Counterparties",
                intelligence.get(
                    "unique_counterparties",
                    0
                )
            )

        st.info(
            intelligence.get(
                "summary",
                "No summary available."
            )
        )

        # =================================================
        # DETECTED PATTERNS
        # =================================================

        st.markdown(
            "### 🔍 Detected Patterns"
        )

        pattern_labels = {

            "large_value_transfer":
                "💰 Large Value Transfers",

            "rapid_fund_movement":
                "⚡ Rapid Fund Movement",

            "multiple_counterparties":
                "👥 Multiple Counterparties",

            "repeated_counterparty":
                "🔁 Repeated Counterparty",

            "incoming_outgoing_flow":
                "🔄 Incoming → Outgoing Flow",

            "unusual_value_pattern":
                "📈 Unusual Value Pattern",
        }

        pattern_counts = intelligence.get(
            "pattern_counts",
            {}
        )

        active_pattern_found = False

        for pattern, count in pattern_counts.items():

            if count > 0:

                active_pattern_found = True

                st.write(
                    f"**{pattern_labels.get(pattern, pattern)}:** "
                    f"{count}"
                )

        if not active_pattern_found:

            st.caption(
                "No detected patterns in the available transaction data."
            )

        # =================================================
        # TRANSACTION FINDINGS
        # =================================================

        st.markdown(
            "### 🚨 Transaction Findings"
        )

        findings = intelligence.get(
            "findings",
            []
        )

        if findings:

            for finding in findings:

                flags = finding.get(
                    "flags",
                    []
                )

                readable_flags = [

                    flag.replace(
                        "_",
                        " "
                    ).title()

                    for flag in flags
                ]

                title = " • ".join(
                    readable_flags
                )

                transaction_index = finding.get(
                    "transaction_index"
                )

                if transaction_index is None:

                    label = "Wallet-Level Finding"

                else:

                    label = (
                        f"Transaction #{transaction_index}"
                    )

                with st.expander(
                    f"{label} — {title}"
                ):

                    st.write(
                        "**Transaction Hash:** "
                        f"`{finding.get('transaction_hash', 'N/A')}`"
                    )

                    st.write(
                        "**From:** "
                        f"`{finding.get('from', '')}`"
                    )

                    st.write(
                        "**To:** "
                        f"`{finding.get('to', '')}`"
                    )

                    value = finding.get(
                        "value",
                        0
                    )

                    try:

                        value_display = f"{float(value):g}"

                    except (TypeError, ValueError):

                        value_display = str(value)

                    st.write(
                        f"**Value:** {value_display}"
                    )

                    explanations = finding.get(
                        "explanations",
                        []
                    )

                    st.markdown(
                        "**Why it was flagged:**"
                    )

                    for explanation in explanations:

                        st.write(
                            f"• {explanation}"
                        )

        else:

            st.success(
                "No transaction-level findings require review."
            )

        # =================================================
        # FUND FLOW
        # =================================================

        st.markdown("---")

        st.markdown(
            "### 🕸️ Fund Flow Intelligence"
        )

        if transactions:

            graph_html, valid_count = build_premium_graph(
                transactions,
                target_wallet
            )

            if valid_count > 0:

                components.html(
                    graph_html,
                    height=740,
                    scrolling=False,
                )

            else:

                st.warning(
                    "Transactions were returned, but no sender/receiver "
                    "addresses were found in the transaction records. "
                    "The graph needs transaction records containing "
                    "'from' and 'to' addresses."
                )

        else:

            st.info(
                "No transaction data was returned "
                "for graph visualization."
            )


# =========================================================
# INVESTIGATION OVERVIEW
# =========================================================

overview_result = st.session_state.get(
    "investigation_result",
    {}
)

if isinstance(overview_result, dict):

    overview_transactions = overview_result.get(
        "transactions",
        []
    )

    overview_target_wallet = overview_result.get(
        "wallet_address",
        ""
    )

else:

    overview_transactions = []

    overview_target_wallet = ""


st.markdown(
    "### Investigation Overview"
)


# =========================================================
# UNIQUE WALLETS
# =========================================================

unique_wallets = set()


for tx in overview_transactions:

    if not isinstance(tx, dict):
        continue

    sender = get_sender(tx)

    receiver = get_receiver(tx)

    if sender:

        unique_wallets.add(
            sender.lower()
        )

    if receiver:

        unique_wallets.add(
            receiver.lower()
        )


if overview_target_wallet:

    unique_wallets.add(
        str(
            overview_target_wallet
        ).lower()
    )


wallets_analyzed = len(
    unique_wallets
)


# =========================================================
# HIGH-RISK SIGNAL
# =========================================================

high_risk_findings = 0


for tx in overview_transactions:

    if not isinstance(tx, dict):
        continue

    value = get_transaction_value(tx)

    try:

        value = float(value)

        if value > 1:

            high_risk_findings += 1

    except (TypeError, ValueError):

        pass


# =========================================================
# VASP
# =========================================================

vasp_matches = 0


# =========================================================
# OVERVIEW CARDS
# =========================================================

c1, c2, c3, c4 = st.columns(4)


with c1:

    st.html(
        f"""
        <div class="metric-card">

            <div class="metric-label">
                Active Cases
            </div>

            <div class="metric-value">
                {1 if overview_transactions else 0}
            </div>

            <div style="
                color:#64748b;
                font-size:0.68rem;
                margin-top:5px;
            ">
                Current investigation
            </div>

        </div>
        """
    )


with c2:

    st.html(
        f"""
        <div class="metric-card">

            <div class="metric-label">
                Wallets Analyzed
            </div>

            <div class="metric-value">
                {wallets_analyzed}
            </div>

            <div style="
                color:#64748b;
                font-size:0.68rem;
                margin-top:5px;
            ">
                Unique addresses
            </div>

        </div>
        """
    )


with c3:

    st.html(
        f"""
        <div class="metric-card">

            <div class="metric-label">
                High-Risk Findings
            </div>

            <div class="metric-value">
                {high_risk_findings}
            </div>

            <div style="
                color:#64748b;
                font-size:0.68rem;
                margin-top:5px;
            ">
                Prototype signal
            </div>

        </div>
        """
    )


with c4:

    st.html(
        f"""
        <div class="metric-card">

            <div class="metric-label">
                VASP Matches
            </div>

            <div class="metric-value">
                {vasp_matches}
            </div>

            <div style="
                color:#64748b;
                font-size:0.68rem;
                margin-top:5px;
            ">
                Known service matches
            </div>

        </div>
        """
    )


# =========================================================
# FOOTER
# =========================================================

st.html(
    """
    <div class="footer">

        CryptoShield · Blockchain Intelligence Prototype
        · SIH 26183

    </div>
    """
)