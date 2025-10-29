"""
Formula Formatter Utilities
Helper functions to create beautifully formatted formula explanations as Dash HTML components.
"""

from dash import html


def create_formula_display(
    title: str,
    formula: str,
    components: list = None,
    tiers: list = None,
    notes: list = None
):
    """
    Create a beautifully formatted formula display.

    Args:
        title: Main title of the formula
        formula: The mathematical formula string
        components: List of (name, description) tuples for formula components
        tiers: List of (range, label, description) tuples for tier breakdowns
        notes: List of additional notes/explanations

    Returns:
        Dash HTML component with formatted formula
    """
    elements = []

    # Title
    elements.append(html.H5(title, className="mb-3 text-primary"))

    # Main formula
    elements.append(html.Div([
        html.Strong("Formula:", className="d-block mb-2"),
        html.Div(
            formula,
            className="p-3 bg-light border-start border-primary border-4 mb-3",
            style={"fontFamily": "monospace", "fontSize": "1.1em"}
        )
    ]))

    # Components breakdown
    if components:
        elements.append(html.H6("Components:", className="mt-3 mb-2"))
        component_items = []
        for name, desc in components:
            component_items.append(
                html.Li([
                    html.Strong(f"{name}: ", className="text-primary"),
                    html.Span(desc)
                ], className="mb-2")
            )
        elements.append(html.Ul(component_items, className="mb-3"))

    # Tier breakdown
    if tiers:
        elements.append(html.H6("Tier Breakdown:", className="mt-3 mb-2"))
        tier_rows = []
        for range_val, label, desc in tiers:
            tier_rows.append(html.Tr([
                html.Td(html.Code(range_val, className="text-nowrap")),
                html.Td(html.Strong(label)),
                html.Td(desc)
            ]))
        elements.append(
            html.Table([
                html.Thead(html.Tr([
                    html.Th("Range"),
                    html.Th("Label"),
                    html.Th("Description")
                ]), className="table-light"),
                html.Tbody(tier_rows)
            ], className="table table-sm table-bordered mb-3")
        )

    # Additional notes
    if notes:
        elements.append(html.H6("Notes:", className="mt-3 mb-2"))
        note_items = []
        for note in notes:
            note_items.append(html.Li(note, className="mb-1"))
        elements.append(html.Ul(note_items, className="mb-0"))

    return html.Div(elements)


def create_simple_formula(title: str, formula: str, description: str = ""):
    """Create a simple formula display with title, formula, and description."""
    elements = [
        html.H5(title, className="mb-3 text-primary"),
        html.Div([
            html.Strong("Formula:", className="d-block mb-2"),
            html.Div(
                formula,
                className="p-3 bg-light border-start border-primary border-4",
                style={"fontFamily": "monospace", "fontSize": "1.1em"}
            )
        ])
    ]

    if description:
        elements.append(html.P(description, className="mt-3 mb-0"))

    return html.Div(elements)


def create_metric_breakdown(
    title: str,
    metric_name: str,
    calculation: str,
    purpose: str = "",
    examples: list = None
):
    """
    Create a metric breakdown display.

    Args:
        title: Title of the metric
        metric_name: Name of the metric
        calculation: How it's calculated
        purpose: Purpose/use of the metric
        examples: List of example calculations

    Returns:
        Formatted Dash HTML component
    """
    elements = [
        html.H5(title, className="mb-3 text-primary"),
        html.Div([
            html.Strong("Metric: ", className="me-2"),
            html.Code(metric_name)
        ], className="mb-2"),
        html.Div([
            html.Strong("Calculation: ", className="me-2"),
            html.Span(calculation)
        ], className="mb-2")
    ]

    if purpose:
        elements.append(html.Div([
            html.Strong("Purpose: ", className="me-2"),
            html.Span(purpose)
        ], className="mb-2"))

    if examples:
        elements.append(html.Hr())
        elements.append(html.H6("Examples:", className="mt-2 mb-2"))
        for example in examples:
            elements.append(html.Div(
                example,
                className="p-2 bg-light border-start border-3 border-info mb-2",
                style={"fontFamily": "monospace", "fontSize": "0.9em"}
            ))

    return html.Div(elements)
