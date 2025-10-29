"""
Info Icon Component
Provides an information icon with tooltip on hover and modal on click.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc


def create_info_icon(
    component_id: str,
    tooltip_text: str,
    modal_title: str,
    formula_explanation = None,  # Can be string (markdown) or Dash component (HTML)
    python_code: str = "",
    sql_code: str = ""
):
    """
    Create an info icon with tooltip and modal containing code and explanations.

    Args:
        component_id: Unique ID for this component (used for modal/tooltip IDs)
        tooltip_text: Brief text shown on hover
        modal_title: Title of the modal window
        formula_explanation: Human-readable explanation - can be string or Dash HTML component
        python_code: Python source code
        sql_code: SQL query code

    Returns:
        List containing info icon, tooltip, and modal components
    """
    modal_id = f"{component_id}-modal"
    icon_id = f"{component_id}-icon"
    tooltip_id = f"{component_id}-tooltip"

    # Create tabs for modal content
    tabs = []

    # Formula explanation tab
    if formula_explanation:
        # Check if formula_explanation is a Dash component or string
        if isinstance(formula_explanation, str):
            # Legacy support: render as markdown
            formula_content = dcc.Markdown(
                formula_explanation,
                className="p-3",
                style={"fontSize": "0.95em", "lineHeight": "1.6"}
            )
        else:
            # New format: use Dash HTML components for better formatting
            formula_content = html.Div(
                formula_explanation,
                className="p-3",
                style={"fontSize": "0.95em", "lineHeight": "1.6"}
            )

        tabs.append(dbc.Tab(
            dbc.Card(dbc.CardBody([formula_content]), className="mt-2"),
            label="Formula",
            tab_id="formula"
        ))

    # Python code tab
    if python_code:
        tabs.append(dbc.Tab(
            dbc.Card(dbc.CardBody([
                html.Div([
                    dbc.Button(
                        [html.I(className="fas fa-copy me-2"), "Copy Python Code"],
                        id=f"{component_id}-copy-python",
                        color="secondary",
                        size="sm",
                        className="mb-2"
                    ),
                    dcc.Clipboard(
                        target_id=f"{component_id}-python-code",
                        id=f"{component_id}-clipboard-python"
                    ),
                    dcc.Markdown(
                        f"```python\n{python_code}\n```",
                        id=f"{component_id}-python-code",
                        className="bg-light p-3 rounded",
                        style={"fontSize": "0.85em"}
                    )
                ])
            ]), className="mt-2"),
            label="Python Code",
            tab_id="python"
        ))

    # SQL code tab
    if sql_code:
        tabs.append(dbc.Tab(
            dbc.Card(dbc.CardBody([
                html.Div([
                    dbc.Button(
                        [html.I(className="fas fa-copy me-2"), "Copy SQL Query"],
                        id=f"{component_id}-copy-sql",
                        color="secondary",
                        size="sm",
                        className="mb-2"
                    ),
                    dcc.Clipboard(
                        target_id=f"{component_id}-sql-code",
                        id=f"{component_id}-clipboard-sql"
                    ),
                    dcc.Markdown(
                        f"```sql\n{sql_code}\n```",
                        id=f"{component_id}-sql-code",
                        className="bg-light p-3 rounded",
                        style={"fontSize": "0.85em"}
                    )
                ])
            ]), className="mt-2"),
            label="SQL Query",
            tab_id="sql"
        ))

    # Create the modal
    modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(modal_title)),
        dbc.ModalBody([
            dbc.Tabs(tabs, active_tab="formula" if formula_explanation else "python")
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id=f"{modal_id}-close", className="ms-auto", n_clicks=0)
        )
    ], id=modal_id, size="xl", is_open=False, scrollable=True)

    # Create the info icon with tooltip
    info_icon = html.Span([
        html.I(
            id=icon_id,
            className="fas fa-info-circle ms-2 text-primary",
            style={"cursor": "pointer", "fontSize": "0.9em"}
        ),
        dbc.Tooltip(
            tooltip_text,
            target=icon_id,
            placement="top"
        )
    ])

    return [info_icon, modal]
