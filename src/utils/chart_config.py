"""
Chart configuration utilities.
Standard configuration for all Plotly charts across the dashboard.
"""

# Standard config to remove Plotly watermarks and toolbar
CHART_CONFIG = {
    'displayModeBar': False,  # Remove the mode bar completely
    'displaylogo': False,      # Remove Plotly logo
    'modeBarButtonsToRemove': ['toImage', 'sendDataToCloud'],  # Remove specific buttons if mode bar is shown
    'responsive': True         # Make charts responsive
}

# Alternative config if you want to keep some controls but remove watermark
CHART_CONFIG_MINIMAL = {
    'displaylogo': False,
    'modeBarButtonsToRemove': [
        'sendDataToCloud',
        'autoScale2d',
        'hoverClosestCartesian',
        'hoverCompareCartesian',
        'lasso2d',
        'select2d',
        'toggleSpikelines'
    ],
    'responsive': True
}
