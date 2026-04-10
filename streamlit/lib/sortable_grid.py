import os
import streamlit.components.v1 as components

_COMPONENT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "components", "sortable_grid"
)

_sortable_grid_func = components.declare_component(
    "sortable_grid",
    path=_COMPONENT_DIR,
)


def sortable_grid(items, key=None):
    """
    Griglia drag-and-drop a 2 colonne con card colorate per fascia di posizione
    e tooltip con descrizione al hover.

    items: list di {"testo": str, "descrizione": str}
    Ritorna: lista di stringhe testo nell'ordine corrente (None al primo render).
    """
    return _sortable_grid_func(items=items, key=key, default=None)
