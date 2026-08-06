#!/usr/bin/env python3
"""
Graph-Editor für topologische Navigation (Thema 2)
====================================================

Interaktives Tool zum Setzen von Knoten (Referenzpunkten) und Kanten
("Schienen") auf einer ROS2-Karte (.pgm + .yaml, map_server-Format).

Bedienung:
----------
- LINKSKLICK auf freie Stelle    -> neuer Knoten wird angelegt
                                     (du wirst im Terminal nach einem Namen gefragt)
- LINKSKLICK auf zwei Knoten     -> Kante zwischen ihnen wird erstellt/entfernt
                                     nacheinander (erster Klick = Start markieren,
                                     zweiter Klick auf anderen Knoten = Kante)
- 'd' + Klick auf Knoten         -> Knoten löschen (inkl. aller Kanten)
- 'r' + Klick auf Knoten         -> Knoten umbenennen
- 't' + Klick auf Knoten         -> Knoten als Tür markieren/entmarkieren (is_door)
- 's'                            -> Speichern (nodes.yaml + edges.yaml)
- 'q'                             -> Beenden (fragt vorher, ob gespeichert werden soll)

Koordinatenumrechnung:
-----------------------
Die Karten-YAML (map_server-Format) enthält:
    resolution: <m/pixel>
    origin: [x, y, theta]   # Weltkoordinate der UNTEREN LINKEN Bildecke

Ein Pixel (px, py) mit py gezählt von OBEN (Bildkonvention) wird umgerechnet zu:
    x_world = origin_x + px * resolution
    y_world = origin_y + (image_height - py) * resolution

Nutzung:
--------
    python3 graph_editor.py --map pfad/zur/karte.yaml

Ausgabe:
--------
    nodes.yaml
    edges.yaml
"""

import argparse
import math
import os
import sys

import numpy as np
import yaml
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import tkinter as tk
from tkinter import simpledialog


def ask_text(title, prompt, initialvalue=""):
    """Öffnet ein kleines Popup-Fenster für Texteingabe (statt Terminal-input())."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    value = simpledialog.askstring(title, prompt, initialvalue=initialvalue, parent=root)
    root.destroy()
    return value


class GraphEditor:
    def __init__(self, map_yaml_path, nodes_out="nodes.yaml", edges_out="edges.yaml"):
        self.nodes_out = nodes_out
        self.edges_out = edges_out

        self._load_map(map_yaml_path)

        # nodes: dict name -> {"x": float, "y": float, "is_door": bool}
        self.nodes = {}
        # edges: list of (name1, name2)
        self.edges = []

        self._pending_edge_start = None  # Name des zuletzt geklickten Knotens (für Kante)
        self._mode = None  # None, 'd' (delete), 'r' (rename), 't' (toggle door)

        self._setup_plot()

    # ------------------------------------------------------------------
    # Karte laden
    # ------------------------------------------------------------------
    def _load_map(self, map_yaml_path):
        if not os.path.isfile(map_yaml_path):
            sys.exit(f"Fehler: Karten-YAML nicht gefunden: {map_yaml_path}")

        with open(map_yaml_path, "r") as f:
            map_meta = yaml.safe_load(f)

        base_dir = os.path.dirname(os.path.abspath(map_yaml_path))
        image_path = map_meta.get("image")
        if not os.path.isabs(image_path):
            image_path = os.path.join(base_dir, image_path)

        if not os.path.isfile(image_path):
            sys.exit(f"Fehler: Kartenbild nicht gefunden: {image_path}")

        self.resolution = float(map_meta["resolution"])
        origin = map_meta.get("origin", [0.0, 0.0, 0.0])
        self.origin_x = float(origin[0])
        self.origin_y = float(origin[1])

        img = Image.open(image_path)
        self.img_array = np.array(img.convert("L"))
        self.img_height = self.img_array.shape[0]
        self.img_width = self.img_array.shape[1]

        print(f"Karte geladen: {image_path}")
        print(f"  Größe: {self.img_width} x {self.img_height} px")
        print(f"  Resolution: {self.resolution} m/px")
        print(f"  Origin: ({self.origin_x}, {self.origin_y})")

    # ------------------------------------------------------------------
    # Koordinatenumrechnung
    # ------------------------------------------------------------------
    def pixel_to_world(self, px, py):
        """py in Bildkoordinaten (0 = oben) -> Weltkoordinaten in Metern."""
        x = self.origin_x + px * self.resolution
        y = self.origin_y + (self.img_height - py) * self.resolution
        return x, y

    def world_to_pixel(self, x, y):
        px = (x - self.origin_x) / self.resolution
        py = self.img_height - (y - self.origin_y) / self.resolution
        return px, py

    # ------------------------------------------------------------------
    # Plot / Interaktion
    # ------------------------------------------------------------------
    def _setup_plot(self):
        self.fig, self.ax = plt.subplots(figsize=(12, 9))
        self.ax.imshow(self.img_array, cmap="gray", origin="upper")
        self.ax.set_title(
            "Linksklick: Knoten setzen / verbinden | d+Klick: löschen | "
            "r+Klick: umbenennen | t+Klick: Tür markieren | s: speichern | q: beenden"
        )

        self.fig.canvas.mpl_connect("button_press_event", self._on_click)
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

        self._redraw()
        plt.show()

    def _nearest_node(self, px, py, max_dist_px=15):
        """Findet den nächstgelegenen Knoten zu einem Pixelklick (für Klick auf bestehenden Knoten)."""
        best_name = None
        best_dist = max_dist_px
        for name, data in self.nodes.items():
            npx, npy = self.world_to_pixel(data["x"], data["y"])
            dist = math.hypot(px - npx, py - npy)
            if dist < best_dist:
                best_dist = dist
                best_name = name
        return best_name

    def _on_key(self, event):
        if event.key in ("d", "r", "t"):
            self._mode = event.key
            print(f"Modus: '{event.key}' aktiv -> nächsten Klick auf einen Knoten anwenden")
        elif event.key == "s":
            self.save()
        elif event.key == "q":
            self.save()
            plt.close(self.fig)

    def _on_click(self, event):
        if event.inaxes != self.ax or event.xdata is None:
            return

        px, py = event.xdata, event.ydata
        clicked_node = self._nearest_node(px, py)

        # Sondermodi (löschen / umbenennen / Tür markieren)
        if self._mode == "d":
            if clicked_node:
                self._delete_node(clicked_node)
            self._mode = None
            self._redraw()
            return

        if self._mode == "r":
            if clicked_node:
                new_name = ask_text("Knoten umbenennen", f"Neuer Name für '{clicked_node}':", clicked_node)
                if new_name:
                    new_name = new_name.strip()
                if new_name:
                    self._rename_node(clicked_node, new_name)
            self._mode = None
            self._redraw()
            return

        if self._mode == "t":
            if clicked_node:
                self.nodes[clicked_node]["is_door"] = not self.nodes[clicked_node].get("is_door", False)
                status = "Tür" if self.nodes[clicked_node]["is_door"] else "kein Tür-Knoten"
                print(f"'{clicked_node}' ist jetzt: {status}")
            self._mode = None
            self._redraw()
            return

        # Normaler Modus: neuer Knoten ODER Kante setzen
        if clicked_node:
            # Klick auf bestehenden Knoten -> Kanten-Logik
            if self._pending_edge_start is None:
                self._pending_edge_start = clicked_node
                print(f"Startknoten für Kante: '{clicked_node}' (klicke jetzt Zielknoten)")
            else:
                if clicked_node == self._pending_edge_start:
                    print("Gleicher Knoten -> Kanten-Auswahl abgebrochen")
                    self._pending_edge_start = None
                else:
                    self._toggle_edge(self._pending_edge_start, clicked_node)
                    self._pending_edge_start = None
            self._redraw()
            return

        # Klick auf freie Fläche -> neuer Knoten
        default_name = f"node_{len(self.nodes) + 1}"
        name = ask_text("Neuer Knoten", "Name für neuen Knoten:", default_name)
        if name is None:
            # Dialog abgebrochen (Cancel) -> keinen Knoten anlegen
            print("Abgebrochen: kein Knoten angelegt")
            return
        name = name.strip()
        if not name:
            name = default_name
        if name in self.nodes:
            print(f"Warnung: Name '{name}' existiert bereits, wird überschrieben")

        x, y = self.pixel_to_world(px, py)
        x, y = float(x), float(y)
        self.nodes[name] = {"x": round(x, 3), "y": round(y, 3), "is_door": False}
        print(f"Knoten '{name}' gesetzt bei ({x:.2f}, {y:.2f}) m")
        self._pending_edge_start = None
        self._redraw()

    def _toggle_edge(self, n1, n2):
        edge = tuple(sorted((n1, n2)))
        existing = [e for e in self.edges if tuple(sorted(e)) == edge]
        if existing:
            self.edges.remove(existing[0])
            print(f"Kante '{n1}' <-> '{n2}' entfernt")
        else:
            self.edges.append((n1, n2))
            print(f"Kante '{n1}' <-> '{n2}' hinzugefügt")

    def _delete_node(self, name):
        del self.nodes[name]
        self.edges = [e for e in self.edges if name not in e]
        print(f"Knoten '{name}' und zugehörige Kanten gelöscht")

    def _rename_node(self, old_name, new_name):
        self.nodes[new_name] = self.nodes.pop(old_name)
        self.edges = [
            (new_name if a == old_name else a, new_name if b == old_name else b)
            for a, b in self.edges
        ]
        print(f"'{old_name}' -> '{new_name}' umbenannt")

    # ------------------------------------------------------------------
    # Zeichnen
    # ------------------------------------------------------------------
    def _redraw(self):
        self.ax.clear()
        self.ax.imshow(self.img_array, cmap="gray", origin="upper")

        # Kanten zeichnen
        for n1, n2 in self.edges:
            if n1 in self.nodes and n2 in self.nodes:
                p1 = self.world_to_pixel(self.nodes[n1]["x"], self.nodes[n1]["y"])
                p2 = self.world_to_pixel(self.nodes[n2]["x"], self.nodes[n2]["y"])
                self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], "b-", linewidth=1.5, zorder=2)

        # Knoten zeichnen
        for name, data in self.nodes.items():
            px, py = self.world_to_pixel(data["x"], data["y"])
            color = "orange" if data.get("is_door") else "red"
            marker = "s" if data.get("is_door") else "o"
            self.ax.plot(px, py, marker=marker, color=color, markersize=9, zorder=3)
            self.ax.text(px + 5, py - 5, name, color=color, fontsize=8, zorder=4)

        legend_handles = [
            mpatches.Patch(color="red", label="Knoten"),
            mpatches.Patch(color="orange", label="Tür-Knoten"),
        ]
        self.ax.legend(handles=legend_handles, loc="upper right", fontsize=8)

        self.ax.set_title(
            "Linksklick: Knoten setzen/verbinden | d+Klick: löschen | "
            "r+Klick: umbenennen | t+Klick: Tür markieren | s: speichern | q: beenden"
        )
        self.fig.canvas.draw_idle()

    # ------------------------------------------------------------------
    # Speichern
    # ------------------------------------------------------------------
    def save(self):
        nodes_data = {
            "nodes": {
                name: {
                    "x": float(data["x"]),
                    "y": float(data["y"]),
                    "is_door": bool(data.get("is_door", False)),
                }
                for name, data in self.nodes.items()
            }
        }
        edges_data = {"edges": [[n1, n2] for n1, n2 in self.edges]}

        with open(self.nodes_out, "w", encoding="utf-8") as f:
            yaml.dump(nodes_data, f, allow_unicode=True, sort_keys=False)
        with open(self.edges_out, "w", encoding="utf-8") as f:
            yaml.dump(edges_data, f, allow_unicode=True, sort_keys=False)

        print(f"Gespeichert: {self.nodes_out} ({len(self.nodes)} Knoten)")
        print(f"Gespeichert: {self.edges_out} ({len(self.edges)} Kanten)")


def main():
    parser = argparse.ArgumentParser(description="Graph-Editor für topologische Navigation")
    parser.add_argument("--map", required=True, help="Pfad zur Karten-YAML (map_server-Format)")
    parser.add_argument("--nodes-out", default="nodes.yaml", help="Ausgabedatei für Knoten")
    parser.add_argument("--edges-out", default="edges.yaml", help="Ausgabedatei für Kanten")
    args = parser.parse_args()

    GraphEditor(args.map, nodes_out=args.nodes_out, edges_out=args.edges_out)


if __name__ == "__main__":
    main()
