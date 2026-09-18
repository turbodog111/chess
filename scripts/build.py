#!/usr/bin/env python3
"""Build static HTML pages for the Queen's Gambit continuation site."""
from __future__ import annotations

import html
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path = [
    p
    for p in sys.path
    if p not in ("", ".")
    and os.path.abspath(p)
    not in (os.path.abspath(ROOT), os.path.abspath(os.path.dirname(ROOT)))
]

import chess  # noqa: E402

PIECE_FILE = {
    chess.PAWN: "P",
    chess.KNIGHT: "N",
    chess.BISHOP: "B",
    chess.ROOK: "R",
    chess.QUEEN: "Q",
    chess.KING: "K",
}

NAV = [
    ("index.html", "Overview"),
    ("qga.html", "Accepted"),
    ("qgd.html", "Declined"),
    ("slav.html", "Slav"),
]


def play(moves: str) -> tuple[chess.Board, list[str], chess.Move | None]:
    board = chess.Board()
    sans: list[str] = []
    last = None
    for san in moves.split():
        last = board.parse_san(san)
        sans.append(board.san(last))
        board.push(last)
    return board, sans, last


def format_moves(sans: list[str]) -> str:
    bits = []
    for i, san in enumerate(sans):
        if i % 2 == 0:
            bits.append(f'<span class="n">{i // 2 + 1}.</span> ')
        cls = ' class="last"' if i == len(sans) - 1 else ""
        bits.append(f"<span{cls}>{html.escape(san)}</span> ")
    return f'<p class="moves">{"".join(bits).rstrip()}</p>'


def render_board(board: chess.Board, last: chess.Move | None, caption: str, compact: bool = False) -> str:
    last_from = last.from_square if last else None
    last_to = last.to_square if last else None
    squares = []
    for rank in range(7, -1, -1):
        for file in range(8):
            sq = chess.square(file, rank)
            dark = (file + rank) % 2 == 0
            cls = ["sq", "d" if dark else "l"]
            if sq == last_from:
                cls.append("last-from")
            if sq == last_to:
                cls.append("last-to")
            piece = board.piece_at(sq)
            inner = ""
            if piece:
                color = "w" if piece.color == chess.WHITE else "b"
                name = PIECE_FILE[piece.piece_type]
                inner = f'<img src="pieces/{color}{name}.svg" alt="">'
            squares.append(f'<div class="{" ".join(cls)}">{inner}</div>')
    turn = "White to move" if board.turn == chess.WHITE else "Black to move"
    label = html.escape(f"{caption}. {turn}.")
    compact_cls = " compact" if compact else ""
    ranks = "".join(f"<span>{r}</span>" for r in range(8, 0, -1))
    files = "".join(f"<span>{f}</span>" for f in "abcdefgh")
    return f"""<figure class="diagram{compact_cls}">
  <div class="diagram-inner">
    <div class="ranks" aria-hidden="true">{ranks}</div>
    <div class="board" role="img" aria-label="{label}">{"".join(squares)}</div>
    <div class="files" aria-hidden="true">{files}</div>
  </div>
  <figcaption><strong>{html.escape(caption)}</strong> · {turn}</figcaption>
</figure>"""


def explorer(prefix: str, variations: list[dict]) -> str:
    inputs = []
    tabs = []
    panels = []
    rules = []
    for i, var in enumerate(variations):
        vid = f"{prefix}-{var['id']}"
        checked = " checked" if i == 0 else ""
        inputs.append(
            f'<input class="exp-input" type="radio" name="{html.escape(prefix)}-line" id="{vid}"{checked}>'
        )
        tabs.append(
            f'<label class="exp-tab" for="{vid}">{html.escape(var["name"])}<small>{html.escape(var["eco"])}</small></label>'
        )
        rules.append(f"#{vid}:checked ~ .exp-tabs label[for='{vid}']")
        board, sans, last = play(var["moves"])
        white = "".join(f"<li>{html.escape(x)}</li>" for x in var["white"])
        black = "".join(f"<li>{html.escape(x)}</li>" for x in var["black"])
        branches = "".join(
            f'<li><span class="mv">{html.escape(b["moves"])}</span><span>{html.escape(b["note"])}</span></li>'
            for b in var.get("branches", [])
        )
        branch_block = f"<ul class='branches'>{branches}</ul>" if branches else ""
        panels.append(
            f"""<article class="exp-panel" data-for="{vid}">
  {render_board(board, last, var["caption"])}
  <div class="line-copy">
    <h3>{html.escape(var["name"])}</h3>
    <p class="eco">{html.escape(var["eco"])}</p>
    {format_moves(sans)}
    <p class="idea">{html.escape(var["idea"])}</p>
    <div class="plans">
      <div class="plan white"><h4>White</h4><ul>{white}</ul></div>
      <div class="plan black"><h4>Black</h4><ul>{black}</ul></div>
    </div>
    {branch_block}
  </div>
</article>"""
        )
        rules.append(f"#{vid}:checked ~ .exp-panels [data-for='{vid}']")
    tab_css = ",\n".join(rules[0::2]) + """ {
  background: var(--forest);
  color: var(--cream);
  border-color: var(--forest);
}
""" + ",\n".join(x + " small" for x in rules[0::2]) + " { color: var(--gold-2); }\n"
    panel_css = ",\n".join(rules[1::2]) + " { display: grid; }\n"
    return f"""<style>
{tab_css}{panel_css}</style>
<section class="explorer" aria-label="Main continuations">
  {"".join(inputs)}
  <div class="exp-tabs" role="tablist">{"".join(tabs)}</div>
  <div class="exp-panels">{"".join(panels)}</div>
</section>"""


def page_shell(title: str, current: str, body: str, description: str) -> str:
    nav = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == current else ""
        nav.append(f'<a href="{href}"{cur}>{label}</a>')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}">
  <meta name="theme-color" content="#1b3a31">
  <link rel="icon" href="pieces/wN.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500&family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="wrap">
      <a class="wordmark" href="index.html">2.c4 <small>Queen's Gambit</small></a>
      <nav class="site-nav" aria-label="Openings">{"".join(nav)}</nav>
    </div>
  </header>
  <main id="main">
    {body}
  </main>
  <footer class="site-footer">
    <div class="wrap">
      <p>A reference to the Queen's Gambit family. Last moves are marked on each diagram.</p>
      <p>Piece drawings by Colin M.L. Burnett, <a href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</a>.</p>
    </div>
  </footer>
</body>
</html>
"""


QGA = [
    {
        "id": "classical",
        "name": "Classical",
        "eco": "D26–D27",
        "moves": "d4 d5 c4 dxc4 Nf3 Nf6 e3 e6 Bxc4 c5 O-O a6",
        "caption": "Classical Queen's Gambit Accepted, after 6...a6",
        "idea": "White recovers the pawn and castles. Black's ...c5 and ...a6 prepare queenside expansion and a fight over whether White is left with an isolated queen's pawn after ...cxd4.",
        "white": [
            "Hold d4 or take on c5 and play against the hanging pawns.",
            "Typical bishop parks: Bb3 or a4 to restrain ...b5.",
        ],
        "black": [
            "Free the position with ...cxd4 or ...b5.",
            "Develop the queenside with ...Nc6, ...Be7, and ...O-O.",
        ],
        "branches": [
            {"moves": "7.Bb3", "note": "Main line. The bishop leaves the c-file and eyes f7."},
            {"moves": "7.a4", "note": "Stops ...b5. Black often answers ...Nc6 and ...Be7."},
            {"moves": "7.dxc5 Qxd1 8.Rxd1 Bxc5", "note": "Queens off. A quiet endgame where Black is comfortable."},
            {"moves": "7.Qe2", "note": "Old main line, connecting the rooks and watching e5."},
        ],
    },
    {
        "id": "central",
        "name": "Central",
        "eco": "D20",
        "moves": "d4 d5 c4 dxc4 e4 e5 Nf3 exd4 Bxc4 Nc6",
        "caption": "Central Variation, after 5...Nc6",
        "idea": "White grabs the centre with 3.e4 instead of the quiet 3.Nf3. Black's 3...e5 is the principled strike. The position opens quickly and both kings can be caught in the middle.",
        "white": [
            "Castle short, then use the extra space and the c4-bishop.",
            "If Black keeps the extra pawn on d4, pressure it with c3 or Nb1-d2.",
        ],
        "black": [
            "Return the pawn to finish development with ...Nf6 and ...Be7.",
            "Do not cling to d4 if it costs several tempi.",
        ],
        "branches": [
            {"moves": "3...Nf6 4.e5 Nd5", "note": "Black refuses 3...e5 and plays against the e-pawn instead."},
            {"moves": "3...Nc6", "note": "Pressures d4 at once. White usually continues Nf3 and d5."},
            {"moves": "3...c5", "note": "A Sicilian-flavoured try; 4.d5 closes the centre in White's favour."},
        ],
    },
    {
        "id": "furman",
        "name": "Furman",
        "eco": "D24",
        "moves": "d4 d5 c4 dxc4 Nf3 Nf6 Nc3 a6 e4 b5 e5 Nd5",
        "caption": "Furman Variation, after 6...Nd5",
        "idea": "White develops both knights and seizes e4-e5 before recovering the c-pawn. Black holds the extra pawn with ...a6 and ...b5. The game becomes a race: White's centre versus Black's queenside mass.",
        "white": [
            "Use e5 to drive the knight and attack on the kingside.",
            "Break the pawn chain with a4 before Black consolidates.",
        ],
        "black": [
            "Keep the extra pawn and challenge the centre with ...c5 or ...e6.",
            "Watch the a8-h1 diagonal once the b-pawn has advanced.",
        ],
        "branches": [
            {"moves": "5.a4", "note": "Restrains ...b5. Can transpose toward QGA two-knights lines."},
            {"moves": "5.e3", "note": "Quieter recovery of the pawn, closer to the Classical."},
            {"moves": "7.a4 e6", "note": "The usual follow-up after 6...Nd5."},
        ],
    },
    {
        "id": "alekhine",
        "name": "Alekhine",
        "eco": "D22",
        "moves": "d4 d5 c4 dxc4 Nf3 a6 e3 b5 a4 Bb7",
        "caption": "Alekhine Variation, after 5...Bb7",
        "idea": "Black delays ...Nf6 and grabs queenside space at once. The light-squared bishop comes to b7. White's a4 asks whether the pawn chain will hold.",
        "white": [
            "Undermine b5 with axb5 or a5, then recover c4.",
            "Play Bxc4, Qe2, and O-O before Black organises ...c5.",
        ],
        "black": [
            "Support b5 with ...c6 if White takes on b5.",
            "Strike in the centre with ...e6 and ...c5 rather than hunting pawns.",
        ],
        "branches": [
            {"moves": "4.e4", "note": "Sharper. White occupies the centre and dares Black to keep the pawn."},
            {"moves": "5.b3", "note": "A flank way to recover c4, less common than a4."},
            {"moves": "6.b3", "note": "After 5...Bb7, White can still undermine from the other side."},
        ],
    },
    {
        "id": "quiet",
        "name": "Old / 3.e3",
        "eco": "D20",
        "moves": "d4 d5 c4 dxc4 e3 e5 Bxc4 exd4 exd4 Nf6",
        "caption": "Quiet Variation, after 5...Nf6",
        "idea": "White recovers the pawn without occupying e4. Black's 3...e5 equalises in many lines by exchanging in the centre. The resulting IQP positions are milder than the Classical.",
        "white": [
            "Treat it as an isolated queen's pawn: pieces to e5 and c5, rook to e1.",
            "Castle short and do not rush d5 unless the tactics are ready.",
        ],
        "black": [
            "Blockade d4 with ...Nd5 or ...Be7-f6.",
            "Trade pieces; the IQP is weaker in the ending.",
        ],
        "branches": [
            {"moves": "3...Nf6", "note": "Declines the immediate ...e5 and transposes toward Classical ground."},
            {"moves": "3...e5 4.Nf3", "note": "White can delay Bxc4 and keep options on d4."},
        ],
    },
]

QGD = [
    {
        "id": "orthodox",
        "name": "Orthodox",
        "eco": "D60–D69",
        "moves": "d4 d5 c4 e6 Nc3 Nf6 Bg5 Be7 e3 O-O Nf3 Nbd7",
        "caption": "Orthodox Queen's Gambit Declined, after 6...Nbd7",
        "idea": "The classical QGD. Black is solid, the light-squared bishop is still in the box, and the centre will be resolved by ...dxc4 or ...c6. Capablanca's releasing manoeuvre ...dxc4 and ...Nd5 is the historic main line.",
        "white": [
            "Rc1, Bd3, and pressure the c-file after ...dxc4.",
            "Keep a grip on e4 so Black cannot free with ...e5.",
        ],
        "black": [
            "Play ...c6, take on c4, then ...Nd5 to swap a pair of pieces.",
            "Do not sit still: the bad bishop on c8 needs a route via b7 or d7.",
        ],
        "branches": [
            {"moves": "7.Rc1 c6 8.Bd3 dxc4 9.Bxc4 Nd5", "note": "Capablanca's freeing manoeuvre, the old main line."},
            {"moves": "7.Qc2", "note": "Rubinstein. White delays Rc1 and watches e4."},
            {"moves": "7.Bd3", "note": "Allows ...dxc4 with tempo. Still fully playable."},
        ],
    },
    {
        "id": "tartakower",
        "name": "Tartakower",
        "eco": "D58–D59",
        "moves": "d4 d5 c4 e6 Nc3 Nf6 Bg5 Be7 e3 O-O Nf3 h6 Bh4 b6",
        "caption": "Tartakower Variation, after 7...b6",
        "idea": "Black asks the bishop a question with ...h6, then fianchettos. The c8-bishop finally becomes a piece. This has been a world-championship workhorse because it is solid and still has bite.",
        "white": [
            "Take on f6 only if the structure after ...Bxf6 favours a bind.",
            "Play Rc1, Bd3, and cxd5, aiming at hanging pawns on c5 and d5.",
        ],
        "black": [
            "Develop ...Bb7 and ...Nbd7, then choose ...c5 or ...Ne4.",
            "The hanging-pawn structure is a feature, not a bug, if the pieces are active.",
        ],
        "branches": [
            {"moves": "8.Be2 Bb7 9.Bxf6 Bxf6 10.cxd5 exd5", "note": "A main tabiya. Black accepts an IQP or hanging pawns."},
            {"moves": "8.cxd5 Nxd5", "note": "The other recapture, keeping a compact centre."},
            {"moves": "8.Bxf6 Bxf6 9.cxd5 exd5", "note": "Immediate trade. Black's bishop pair compensates."},
        ],
    },
    {
        "id": "lasker",
        "name": "Lasker",
        "eco": "D56–D57",
        "moves": "d4 d5 c4 e6 Nc3 Nf6 Bg5 Be7 e3 O-O Nf3 h6 Bh4 Ne4 Bxe7 Qxe7",
        "caption": "Lasker Defence, after 8...Qxe7",
        "idea": "Black forces a pair of exchanges with ...Ne4. The resulting position is one of the most reliable equalising methods in the QGD: fewer pieces, a sound structure, and a clear plan of ...c6, ...Nxc3, and ...dxc4.",
        "white": [
            "Keep enough pieces on the board to make the space count.",
            "Qc2, Rc1, and Bd3; do not allow a total liquidation.",
        ],
        "black": [
            "Trade on c3, take on c4, and play ...c5 or ...e5 later.",
            "The queen on e7 supports both central breaks.",
        ],
        "branches": [
            {"moves": "9.cxd5 Nxc3 10.bxc3 exd5", "note": "Exchange structure. White has the c-file; Black is very solid."},
            {"moves": "9.Qc2 Nxc3 10.Qxc3", "note": "Keeps more tension. Black continues ...c6 or ...dxc4."},
            {"moves": "9.Rc1", "note": "A useful waiting move before deciding the centre."},
        ],
    },
    {
        "id": "exchange",
        "name": "Exchange",
        "eco": "D35–D36",
        "moves": "d4 d5 c4 e6 Nc3 Nf6 cxd5 exd5 Bg5 c6 Qc2",
        "caption": "Exchange Variation, after 6.Qc2",
        "idea": "White fixes a Carlsbad structure and aims for the minority attack b4-b5. Black can also be attacked in the centre with Nge2 and f3-e4. This is one of White's most practical tries against the QGD.",
        "white": [
            "Minority attack: Rb1, b4, b5, and a weakness on c6.",
            "Or Nge2, f3, e4 if Black commits to a kingside fianchetto.",
        ],
        "black": [
            "Meet b4-b5 with ...a5, ...b5, or a knight on d6.",
            "Kingside play with ...Ne4, ...f5, and ...Bd6 is the other plan.",
        ],
        "branches": [
            {"moves": "6.e3 Bf5", "note": "The old line. Qc2 is designed to stop this bishop sortie."},
            {"moves": "5.Bf4", "note": "Modern Exchange. White avoids Bg5 and keeps the bishop pair options."},
            {"moves": "6...g6 7.e3 Bf5", "note": "Black develops the bishop anyway and fianchettos later."},
        ],
    },
    {
        "id": "cambridge",
        "name": "Cambridge Springs",
        "eco": "D52",
        "moves": "d4 d5 c4 e6 Nc3 Nf6 Bg5 Nbd7 e3 c6 Nf3 Qa5",
        "caption": "Cambridge Springs, after 6...Qa5",
        "idea": "Black leaves the f8-bishop at home and pins Nc3 with ...Qa5. The tactical point is ...Bb4 and ...Ne4, hitting c3 and g5. Named for the 1904 tournament, it is still a sound surprise weapon.",
        "white": [
            "Nd2 unpins and covers e4. Then a3 or cxd5.",
            "Do not grab on d5 too early if ...Bb4 and ...Ne4 are both in.",
        ],
        "black": [
            "Play ...Bb4, ...Ne4, and sometimes ...dxc4.",
            "If White is careless, the bishop on g5 hangs after ...Ne4.",
        ],
        "branches": [
            {"moves": "7.Nd2 Bb4 8.Qc2", "note": "Main line. White overprotects c3."},
            {"moves": "7.cxd5 Nxd5", "note": "Opens the queen's pin. Tactics on c3 follow."},
            {"moves": "7.Bxf6 Nxf6 8.Bd3", "note": "Gives up the bishop pair to kill the ...Ne4 idea."},
        ],
    },
    {
        "id": "ragozin",
        "name": "Ragozin",
        "eco": "D38",
        "moves": "d4 d5 c4 e6 Nc3 Nf6 Nf3 Bb4 cxd5 exd5 Bg5 h6",
        "caption": "Ragozin Defence, after 6...h6",
        "idea": "Black pins the knight with ...Bb4 instead of the meek ...Be7. The line is more active than the Orthodox and is a favourite of players who want a fight from a QGD move order.",
        "white": [
            "Qa4+ or e3 and Bd3, forcing Black to decide the bishop.",
            "Take on f6 and double Black's pawns if the king stays in the centre.",
        ],
        "black": [
            "Castle, then ...c5 or ...Nbd7-b6.",
            "Keep the pin until White spends time with a3.",
        ],
        "branches": [
            {"moves": "5.Bg5 dxc4", "note": "Vienna mix. Black takes on c4 after the pin is in."},
            {"moves": "5.e3 O-O 6.Bd3", "note": "A quieter Ragozin, often transposing to a Nimzo structure."},
            {"moves": "6.Bh4", "note": "Keeps the pin. Black continues ...c5 or ...Nbd7."},
        ],
    },
    {
        "id": "tarrasch",
        "name": "Tarrasch",
        "eco": "D32–D34",
        "moves": "d4 d5 c4 e6 Nc3 c5 cxd5 exd5 Nf3 Nc6 g3 Nf6 Bg2",
        "caption": "Tarrasch Defence, after 7.Bg2",
        "idea": "Black hits back with ...c5 and accepts an isolated queen's pawn. The pieces get free play; the pawn on d5 is the long-term bill. The Rubinstein system with g3 is White's most respected answer.",
        "white": [
            "Blockade d4, pressure d5, and trade into a favourable ending.",
            "Bg2, O-O, and often Bg5 or Na4-c5.",
        ],
        "black": [
            "Activity first: ...Be7, ...O-O, ...Re8, and ...Bg4.",
            "The IQP is a weapon while pieces remain.",
        ],
        "branches": [
            {"moves": "6.g3 Nf6 7.Bg2 Be7 8.O-O O-O", "note": "Main Rubinstein Tarrasch."},
            {"moves": "4.e3 Nf6 5.Nf3 Nc6", "note": "Symmetrical Tarrasch; less isolated-pawn play."},
            {"moves": "3...Nf6 4.Nf3 c5", "note": "Semi-Tarrasch, usually with ...cxd4 rather than an IQP."},
        ],
    },
]

SLAV = [
    {
        "id": "czech",
        "name": "Czech Main Line",
        "eco": "D18–D19",
        "moves": "d4 d5 c4 c6 Nf3 Nf6 Nc3 dxc4 a4 Bf5 e3 e6 Bxc4 Bb4 O-O",
        "caption": "Czech Slav, after 8.O-O",
        "idea": "The main Slav. Black takes on c4 only after White's knight is on c3, then develops the problem bishop to f5 before closing the chain with ...e6. White's a4 stops ...b5.",
        "white": [
            "Qe2, Rd1, and e4, building a broad centre.",
            "Nh4 can hunt the f5-bishop if Black is slow.",
        ],
        "black": [
            "Castle, then ...Nbd7 and ...a6 or ...Qe7.",
            "The bishop on f5 is the point of the opening — do not bury it.",
        ],
        "branches": [
            {"moves": "8...O-O 9.Qe2 Nbd7 10.e4", "note": "Classical main line. Black often replies ...Bg6."},
            {"moves": "6.Ne5", "note": "Krause Attack, a different tabiya (see next line)."},
            {"moves": "6.Nh4", "note": "Asks the bishop a question before e3 is played."},
        ],
    },
    {
        "id": "krause",
        "name": "Krause",
        "eco": "D17",
        "moves": "d4 d5 c4 c6 Nf3 Nf6 Nc3 dxc4 a4 Bf5 Ne5 Nbd7 Nxc4 Qc7",
        "caption": "Krause Attack, after 7...Qc7",
        "idea": "Instead of recovering the pawn with e3 and Bxc4, White hops Ne5 and takes on c4 with the knight. The position is more open. Black's queen comes to c7 to support ...e5.",
        "white": [
            "g3, Bg2, and O-O, or Bf4 hitting the queen.",
            "Control e5 so Black cannot liquidate the centre.",
        ],
        "black": [
            "Strike with ...e5. If dxe5 Nxe5, the pieces come out fast.",
            "Keep the f5-bishop; it is the best piece in the position.",
        ],
        "branches": [
            {"moves": "8.g3 e5 9.dxe5 Nxe5 10.Bf4", "note": "A main tabiya of the Krause."},
            {"moves": "8.Bg5", "note": "Pins the knight and delays g3."},
            {"moves": "6...e6 7.f3", "note": "Wiesbaden Variation, a sharper cousin of the Krause."},
        ],
    },
    {
        "id": "exchange",
        "name": "Exchange",
        "eco": "D13–D14",
        "moves": "d4 d5 c4 c6 cxd5 cxd5 Nc3 Nf6 Nf3 Nc6 Bf4",
        "caption": "Exchange Slav, after 6.Bf4",
        "idea": "White kills the Slav's counterplay and plays for two results. The structure is symmetrical. Small advantages come from the better bishop and a minority idea on the queenside.",
        "white": [
            "Qb3 or Rc1, pressure b7, and a knight toward b5 or e5.",
            "Do not allow ...Bf5 and ...e6 with total comfort.",
        ],
        "black": [
            "Develop ...Bf5 or ...Bg4, then ...e6 and ...Bd6.",
            "Equalise by trading the right minor pieces, not all of them.",
        ],
        "branches": [
            {"moves": "6...Bf5 7.e3 e6 8.Qb3", "note": "The old main line, hitting b7."},
            {"moves": "6...a6", "note": "Stops Nb5. A modern, very solid choice."},
            {"moves": "4.Nf3 Nf6 5.Nc3 Nc6 6.Bf4 Nh5", "note": "Black hunts the bishop at once."},
        ],
    },
    {
        "id": "chebanenko",
        "name": "Chebanenko",
        "eco": "D15",
        "moves": "d4 d5 c4 c6 Nf3 Nf6 Nc3 a6 c5 Nbd7 Bf4",
        "caption": "Chebanenko Slav, after 6.Bf4",
        "idea": "Black's 4...a6 is a useful waiting move. It prepares ...b5 and ...Bg4, and it asks White how to occupy the centre. 5.c5 gains space; 5.e3 and 5.a4 are the other main tries.",
        "white": [
            "If 5.c5, clamp the queenside and play Bf4, h3, and e3.",
            "If 5.e3, allow ...b5 and fight the queenside expansion.",
        ],
        "black": [
            "Against c5, chip with ...e5 or ...b6.",
            "Against quieter fifth moves, ...b5, ...Bg4, and ...e6.",
        ],
        "branches": [
            {"moves": "5.e3 b5 6.b3", "note": "A standard way to keep a pawn on c4."},
            {"moves": "5.a4 e6 6.Bg5", "note": "Stops ...b5. Can look like a QGD with ...a6 in."},
            {"moves": "5.Ne5", "note": "An aggressive sideline aiming at f7 and c6."},
        ],
    },
    {
        "id": "meran",
        "name": "Meran",
        "eco": "D47–D49",
        "moves": "d4 d5 c4 c6 Nf3 Nf6 Nc3 e6 e3 Nbd7 Bd3 dxc4 Bxc4 b5 Bd3 a6",
        "caption": "Meran Variation, after 8...a6",
        "idea": "The Semi-Slav via 4...e6, then the classical Meran: Black takes on c4 and expands with ...b5 and ...a6. Both sides castle into a heavy-piece fight. This is one of the most analysed families in all of chess.",
        "white": [
            "e4 is the thematic break. Then e5 or a4.",
            "O-O, Qe2, and Rd1 before the centre opens.",
        ],
        "black": [
            "...c5 is the point. The hanging pawns or an IQP may follow.",
            "Develop ...Bb7 and ...Be7; do not delay ...c5 too long.",
        ],
        "branches": [
            {"moves": "9.e4 c5 10.e5", "note": "Reynolds Attack, the sharp old main line."},
            {"moves": "9.O-O c5 10.a4", "note": "A modern attempt to undermine b5 first."},
            {"moves": "6.Qc2", "note": "Anti-Meran. White avoids Bd3 and waits."},
        ],
    },
    {
        "id": "botvinnik",
        "name": "Botvinnik",
        "eco": "D44",
        "moves": "d4 d5 c4 c6 Nf3 Nf6 Nc3 e6 Bg5 dxc4 e4 b5 e5 h6 Bh4 g5 Nxg5",
        "caption": "Botvinnik Variation, after 9.Nxg5",
        "idea": "The most violent Semi-Slav. White's 5.Bg5 and 6.e4 dare Black to keep the extra pawn. After ...h6, ...g5, and Nxg5 the kingside is ripped open. Theory here runs past move twenty.",
        "white": [
            "Sacrifice on g5 is thematic. Hunt the uncastled king.",
            "The pawn on e5 cramps Black's knights.",
        ],
        "black": [
            "Return material to castle long, or run with ...Rg8 and ...g4.",
            "The extra queenside pawns win endings if the king survives.",
        ],
        "branches": [
            {"moves": "9...hxg5 10.Bxg5 Nbd7", "note": "Main continuation. Both sides are committed."},
            {"moves": "8.Bh4 g5 9.exf6 gxh4 10.Ne5", "note": "A related piece of chaos if White takes on f6."},
            {"moves": "5...h6", "note": "Declines the Botvinnik and enters the Moscow instead."},
        ],
    },
    {
        "id": "moscow",
        "name": "Moscow",
        "eco": "D43",
        "moves": "d4 d5 c4 c6 Nf3 Nf6 Nc3 e6 Bg5 h6 Bxf6 Qxf6 e3 Nd7",
        "caption": "Moscow Variation, after 7...Nd7",
        "idea": "Black's 5...h6 asks the bishop to take on f6 or retreat. 6.Bxf6 gives Black the bishop pair in a slightly cramped structure. It is the practical alternative to the Botvinnik.",
        "white": [
            "Bd3, O-O, and Rc1. The bind is worth more than the bishop pair if Black is slow.",
            "A later e4 must be prepared; the dark squares are tender.",
        ],
        "black": [
            "...dxc4, ...b5, and ...c5, using the two bishops.",
            "Do not play ...e5 until development is finished.",
        ],
        "branches": [
            {"moves": "6.Bh4", "note": "Anti-Moscow. White keeps the bishop; Black can still grab dxc4."},
            {"moves": "8.Bd3 dxc4 9.Bxc4 g6", "note": "A modern setup with ...Bg7."},
            {"moves": "7.Qb3", "note": "Hits b7 and slows ...dxc4."},
        ],
    },
    {
        "id": "slow",
        "name": "Slow Slav",
        "eco": "D12",
        "moves": "d4 d5 c4 c6 Nf3 Nf6 e3 Bf5 Nc3 e6 Nh4 Bg6",
        "caption": "Slow Slav, after 6...Bg6",
        "idea": "White delays Nc3 so that ...dxc4 does not come with the usual bite. Black develops the bishop anyway. 6.Nh4 is the standard way to pick up the bishop pair.",
        "white": [
            "Take on g6 when it damages Black's structure, then c5 or Bd3.",
            "A quiet Catalan-like setup with Be2 and O-O is also fine.",
        ],
        "black": [
            "Allow Nxg6 and use the open h-file, or drop back to e4.",
            "...Nbd7, ...Bd6, and ...O-O remain the development scheme.",
        ],
        "branches": [
            {"moves": "5.Nc3 e6 6.Nh4 Be4", "note": "The bishop stays in the centre instead of g6."},
            {"moves": "5.Bd3 Bxd3 6.Qxd3", "note": "Simple chess. White has an easy game and a small pull."},
            {"moves": "4...Bg4", "note": "The other Slow Slav, pinning the knight instead of ...Bf5."},
        ],
    },
]


def write(path: str, text: str) -> None:
    full = os.path.join(ROOT, path)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", path)


def index_page() -> str:
    start_board, _, start_last = play("d4 d5 c4")
    qga_board, _, qga_last = play("d4 d5 c4 dxc4")
    qgd_board, _, qgd_last = play("d4 d5 c4 e6")
    slav_board, _, slav_last = play("d4 d5 c4 c6")
    body = f"""
    <div class="wrap">
      <section class="hero">
        <div>
          <p class="kicker">D06–D69</p>
          <h1>Three answers after 2.c4</h1>
          <p class="lede">White offers the c-pawn on move two. Black can take it, decline it with ...e6, or support the centre with ...c6. This site is a map of the main continuations from that fork.</p>
          <div class="meta-row">
            <span class="badge">1. d4 d5 2. c4</span>
          </div>
        </div>
        {render_board(start_board, start_last, "The Queen's Gambit, after 2.c4")}
      </section>

      <hr class="section-rule">

      <section class="section" id="fork">
        <h2>The fork</h2>
        <p class="deck">Each reply has a different bishop and a different kind of fight. Open a chapter for the full tree.</p>
        <div class="fork-grid">
          <a class="fork-card" href="qga.html">
            {render_board(qga_board, qga_last, "2...dxc4", compact=True)}
            <div>
              <p class="kicker">D20–D29</p>
              <h3>Accepted</h3>
              <p class="reply">2...dxc4</p>
              <p>Black takes the pawn. The centre opens and the light-squared bishop is free. White usually recovers c4 with a lead in development.</p>
              <p class="go">Open the Accepted →</p>
            </div>
          </a>
          <a class="fork-card" href="qgd.html">
            {render_board(qgd_board, qgd_last, "2...e6", compact=True)}
            <div>
              <p class="kicker">D30–D69</p>
              <h3>Declined</h3>
              <p class="reply">2...e6</p>
              <p>Black bolsters d5. The light-squared bishop is shut in, but the centre holds. Orthodox, Exchange, Tartakower, Lasker, Ragozin, Tarrasch.</p>
              <p class="go">Open the Declined →</p>
            </div>
          </a>
          <a class="fork-card" href="slav.html">
            {render_board(slav_board, slav_last, "2...c6", compact=True)}
            <div>
              <p class="kicker">D10–D19</p>
              <h3>Slav</h3>
              <p class="reply">2...c6</p>
              <p>Black supports d5 without locking the bishop. The Czech line is solid; the Semi-Slav can explode. Exchange, Chebanenko, Meran, Botvinnik.</p>
              <p class="go">Open the Slav →</p>
            </div>
          </a>
        </div>
      </section>

      <section class="section" id="compare">
        <h2>At a glance</h2>
        <p class="deck">Same two white moves. Three different games.</p>
        <div style="overflow-x:auto">
          <table class="compare">
            <thead>
              <tr>
                <th></th>
                <th><a href="qga.html">Accepted</a></th>
                <th><a href="qgd.html">Declined</a></th>
                <th><a href="slav.html">Slav</a></th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Reply</td>
                <td>2...dxc4</td>
                <td>2...e6</td>
                <td>2...c6</td>
              </tr>
              <tr>
                <td>c8-bishop</td>
                <td>Free at once</td>
                <td>Shut in by ...e6</td>
                <td>Usually developed to f5 or g4</td>
              </tr>
              <tr>
                <td>Centre</td>
                <td>Open; often an IQP</td>
                <td>Closed, then a minority attack or hanging pawns</td>
                <td>Solid, or a Semi-Slav firefight</td>
              </tr>
              <tr>
                <td>Black's risk</td>
                <td>Falls behind in development</td>
                <td>Gets squeezed if the bishop never enters</td>
                <td>Theory load in the Meran and Botvinnik</td>
              </tr>
              <tr>
                <td>Typical plan</td>
                <td>...c5 and ...a6</td>
                <td>...Nbd7, ...c6, ...dxc4, ...Nd5</td>
                <td>...Bf5 before ...e6, or ...e6 and ...b5</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
    """
    return page_shell(
        "Queen's Gambit — Accepted, Declined, Slav",
        "index.html",
        body,
        "A professional HTML and CSS reference to Queen's Gambit Accepted, Declined, and Slav continuations.",
    )


def opening_page(
    filename: str,
    kicker: str,
    title: str,
    lede: str,
    start_moves: str,
    start_caption: str,
    variations: list[dict],
    prefix: str,
    extra_tree: list[dict],
    description: str,
) -> str:
    board, _, last = play(start_moves)
    tree = "".join(
        f'<li><span class="mv">{html.escape(item["moves"])}</span><div><strong>{html.escape(item["name"])}</strong><p>{html.escape(item["note"])}</p></div></li>'
        for item in extra_tree
    )
    body = f"""
    <div class="wrap">
      <header class="page-head">
        <p class="crumb"><a href="index.html">2.c4</a> · {html.escape(title)}</p>
        <p class="kicker">{html.escape(kicker)}</p>
        <h1>{html.escape(title)}</h1>
        <p class="lede">{html.escape(lede)}</p>
      </header>
      <section class="hero">
        {render_board(board, last, start_caption)}
        <div>
          <h2>How to read the lines</h2>
          <p class="idea">Each tab is a main continuation. The diagram shows the tabiya with the last move marked. Branches under the plans are the usual next forks, not a complete book.</p>
          <ul class="tree">{tree}</ul>
        </div>
      </section>
      <hr class="section-rule">
      <section class="section" id="lines">
        <h2>Main continuations</h2>
        <p class="deck">Choose a line. The board and the plans update together.</p>
        {explorer(prefix, variations)}
      </section>
    </div>
    """
    return page_shell(f"{title} — 2.c4", filename, body, description)


def main() -> None:
    for var_list in (QGA, QGD, SLAV):
        for var in var_list:
            play(var["moves"])

    write("index.html", index_page())
    write(
        "qga.html",
        opening_page(
            "qga.html",
            "D20–D29",
            "Queen's Gambit Accepted",
            "Black takes the offered c-pawn. White almost always recovers it. The fight is about time, the c8-bishop, and whether Black can free the game with ...c5.",
            "d4 d5 c4 dxc4",
            "Queen's Gambit Accepted, after 2...dxc4",
            QGA,
            "qga",
            [
                {"moves": "3.Nf3", "name": "Main recovery", "note": "Stops ...e5. Leads to the Classical, Alekhine, and Furman."},
                {"moves": "3.e4", "name": "Central", "note": "Occupies the centre at once. Black's 3...e5 is the test."},
                {"moves": "3.e3", "name": "Old / Quiet", "note": "Recovers the pawn without a fight for e4."},
            ],
            "Queen's Gambit Accepted continuations: Classical, Central, Furman, Alekhine, and 3.e3.",
        ),
    )
    write(
        "qgd.html",
        opening_page(
            "qgd.html",
            "D30–D69",
            "Queen's Gambit Declined",
            "Black declines the pawn and supports d5 with ...e6. The structure is one of the oldest in chess. White's main tries are Bg5 systems, the Exchange minority attack, and the more active Ragozin and Tarrasch.",
            "d4 d5 c4 e6",
            "Queen's Gambit Declined, after 2...e6",
            QGD,
            "qgd",
            [
                {"moves": "3.Nc3 Nf6 4.Bg5", "name": "Orthodox family", "note": "Be7, Tartakower, Lasker, Cambridge Springs."},
                {"moves": "3.Nc3 Nf6 4.cxd5", "name": "Exchange", "note": "Carlsbad structure and the minority attack."},
                {"moves": "3.Nc3 c5", "name": "Tarrasch", "note": "Black hits the centre and accepts an IQP."},
            ],
            "Queen's Gambit Declined continuations: Orthodox, Tartakower, Lasker, Exchange, Cambridge Springs, Ragozin, Tarrasch.",
        ),
    )
    write(
        "slav.html",
        opening_page(
            "slav.html",
            "D10–D19",
            "Slav Defense",
            "Black supports d5 with ...c6 so the light-squared bishop can still get out. The Czech main line is a model of solidity. The Semi-Slav (4...e6) is the other universe: Meran, Moscow, and the Botvinnik.",
            "d4 d5 c4 c6",
            "Slav Defense, after 2...c6",
            SLAV,
            "slav",
            [
                {"moves": "3.Nf3 Nf6 4.Nc3 dxc4", "name": "Slav Accepted", "note": "Czech main line and the Krause Attack."},
                {"moves": "4...e6", "name": "Semi-Slav", "note": "Meran, Moscow, Botvinnik. Also reachable from the QGD."},
                {"moves": "3.cxd5 cxd5", "name": "Exchange", "note": "Symmetrical, two-result chess."},
            ],
            "Slav Defense continuations: Czech, Krause, Exchange, Chebanenko, Meran, Botvinnik, Moscow, Slow Slav.",
        ),
    )


if __name__ == "__main__":
    main()
