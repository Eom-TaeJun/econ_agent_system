"""
Economics Workflow Templates
Pre-defined workflows for common economic analysis tasks
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum

class WorkflowType(Enum):
    VARIABLE_DISCOVERY = "variable_discovery"
    CORRELATION_ANALYSIS = "correlation_analysis"
    REGRESSION_MODELING = "regression_modeling"
    TIME_SERIES_ANALYSIS = "time_series_analysis"
    CAUSAL_INFERENCE = "causal_inference"
    MACRO_INDICATOR = "macro_indicator"
    CUSTOM = "custom"

@dataclass
class WorkflowTemplate:
    """Template for economic analysis workflows"""
    name: str
    workflow_type: WorkflowType
    description: str
    research_queries: List[str]
    data_requirements: List[str]
    analysis_tasks: List[str]
    expected_outputs: List[str]
    
# Pre-defined templates
TEMPLATES = {
    WorkflowType.VARIABLE_DISCOVERY: WorkflowTemplate(
        name="Meaningful Variable Discovery",
        workflow_type=WorkflowType.VARIABLE_DISCOVERY,
        description="Discover and analyze meaningful economic variables",
        research_queries=[
            "Find key economic indicators and their relationships",
            "Research academic papers on economic variable selection",
            "Identify leading vs lagging indicators"
        ],
        data_requirements=[
            "FRED economic indicators (GDP, CPI, unemployment)",
            "Financial market data (S&P 500, Treasury yields)",
            "Macro data from World Bank/IMF"
        ],
        analysis_tasks=[
            "Calculate correlation matrix for all variables",
            "Perform PCA to identify key factors",
            "Test Granger causality between variables",
            "Create visualization of variable relationships"
        ],
        expected_outputs=[
            "Correlation heatmap",
            "Variable importance ranking",
            "Factor loading table",
            "Causal relationship diagram"
        ]
    ),
    
    WorkflowType.CORRELATION_ANALYSIS: WorkflowTemplate(
        name="Correlation Analysis",
        workflow_type=WorkflowType.CORRELATION_ANALYSIS,
        description="Analyze correlations between economic variables",
        research_queries=[
            "Find research on spurious correlations in economics",
            "Best practices for correlation analysis",
            "Time-lagged correlation methods"
        ],
        data_requirements=[
            "Time series data for target variables",
            "Control variables data",
            "External factors data"
        ],
        analysis_tasks=[
            "Calculate Pearson and Spearman correlations",
            "Test for statistical significance",
            "Analyze rolling correlations over time",
            "Identify structural breaks"
        ],
        expected_outputs=[
            "Correlation matrix with p-values",
            "Rolling correlation charts",
            "Significance test results"
        ]
    ),
    
    WorkflowType.REGRESSION_MODELING: WorkflowTemplate(
        name="Regression Modeling",
        workflow_type=WorkflowType.REGRESSION_MODELING,
        description="Build regression models for economic relationships",
        research_queries=[
            "Best regression techniques for economic data",
            "Variable selection methods (LASSO, Ridge)",
            "Handling multicollinearity"
        ],
        data_requirements=[
            "Dependent variable data",
            "Independent variables data",
            "Instrumental variables if needed"
        ],
        analysis_tasks=[
            "Perform OLS regression",
            "Test regression assumptions",
            "Try regularized regression (LASSO/Ridge)",
            "Cross-validate model performance"
        ],
        expected_outputs=[
            "Regression coefficients table",
            "Model diagnostics",
            "Prediction vs actual plots",
            "Feature importance chart"
        ]
    ),
    
    WorkflowType.TIME_SERIES_ANALYSIS: WorkflowTemplate(
        name="Time Series Analysis",
        workflow_type=WorkflowType.TIME_SERIES_ANALYSIS,
        description="Analyze economic time series data",
        research_queries=[
            "Time series analysis methods for economics",
            "Stationarity testing approaches",
            "ARIMA vs VAR models"
        ],
        data_requirements=[
            "Historical time series data",
            "Frequency-aligned variables",
            "Exogenous variables if needed"
        ],
        analysis_tasks=[
            "Test for stationarity (ADF, KPSS)",
            "Fit ARIMA/SARIMA models",
            "Forecast future values",
            "Decompose trend, seasonality, residuals"
        ],
        expected_outputs=[
            "Stationarity test results",
            "Time series decomposition plots",
            "Forecast charts with confidence intervals",
            "Model comparison metrics"
        ]
    ),
    
    WorkflowType.MACRO_INDICATOR: WorkflowTemplate(
        name="Macroeconomic Indicator Analysis",
        workflow_type=WorkflowType.MACRO_INDICATOR,
        description="Analyze macroeconomic indicators and relationships",
        research_queries=[
            "Key macroeconomic indicators and their definitions",
            "Leading economic indicators",
            "Macro indicator forecasting methods"
        ],
        data_requirements=[
            "GDP and components",
            "Inflation measures (CPI, PCE)",
            "Employment data",
            "Interest rates and yields",
            "Trade data"
        ],
        analysis_tasks=[
            "Create macro dashboard",
            "Analyze indicator trends",
            "Calculate economic surprise indices",
            "Build composite indicators"
        ],
        expected_outputs=[
            "Macro dashboard visualization",
            "Indicator trend analysis",
            "Leading indicator scores",
            "Economic outlook summary"
        ]
    )
}

def get_template(workflow_type: WorkflowType) -> WorkflowTemplate:
    """Get a workflow template by type"""
    return TEMPLATES.get(workflow_type)

def get_all_templates() -> Dict[str, WorkflowTemplate]:
    """Get all available templates"""
    return {wt.value: template for wt, template in TEMPLATES.items()}

def create_custom_template(
    name: str,
    description: str,
    research_queries: List[str],
    data_requirements: List[str],
    analysis_tasks: List[str],
    expected_outputs: List[str]
) -> WorkflowTemplate:
    """Create a custom workflow template"""
    return WorkflowTemplate(
        name=name,
        workflow_type=WorkflowType.CUSTOM,
        description=description,
        research_queries=research_queries,
        data_requirements=data_requirements,
        analysis_tasks=analysis_tasks,
        expected_outputs=expected_outputs
    )

# Common economic variables for reference
COMMON_VARIABLES = {
    "growth": ["GDP", "Real GDP", "GDP Growth Rate", "Industrial Production"],
    "inflation": ["CPI", "Core CPI", "PCE", "PPI", "Inflation Expectations"],
    "employment": ["Unemployment Rate", "NFP", "Initial Claims", "Labor Force Participation"],
    "monetary": ["Fed Funds Rate", "M1", "M2", "Bank Reserves"],
    "financial": ["S&P 500", "VIX", "10Y Treasury", "Credit Spreads", "TED Spread"],
    "trade": ["Trade Balance", "Current Account", "Exchange Rates", "Import/Export Prices"],
    "sentiment": ["Consumer Confidence", "PMI", "ISM", "Business Confidence"],
    "housing": ["Housing Starts", "Building Permits", "Home Prices", "Mortgage Rates"]
}

# FRED series codes for common variables
FRED_CODES = {
    "GDP": "GDP",
    "Real GDP": "GDPC1",
    "CPI": "CPIAUCSL",
    "Core CPI": "CPILFESL",
    "Unemployment": "UNRATE",
    "Fed Funds": "FEDFUNDS",
    "10Y Treasury": "GS10",
    "S&P 500": "SP500",
    "M2": "M2SL",
    "Industrial Production": "INDPRO",
    "Consumer Confidence": "UMCSENT",
    "Housing Starts": "HOUST"
}
