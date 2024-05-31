import os
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.monitor import MonitorManagementClient
import pandas as pd
from pmdarima import auto_arima
import warnings
warnings.filterwarnings("ignore")

# Azure AD application (client) ID
CLIENT_ID = os.environ["AZURE_CLIENT_ID"]

# Azure AD application (client) secret
CLIENT_SECRET = os.environ["AZURE_CLIENT_SECRET"]

# Azure AD tenant ID
TENANT_ID = os.environ["AZURE_TENANT_ID"]

# Authenticate with Azure AD
credential = ClientSecretCredential(
    tenant_id=TENANT_ID,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)

# Get an authenticated token for the resource
RESOURCE_URI = "https://management.azure.com/"
token = credential.get_token(RESOURCE_URI)
headers = {"Authorization": f"Bearer {token.token}"}

# Define resource types and metrics to forecast
resource_types = [
    {
        "type": "Microsoft.Compute/virtualMachines",
        "namespace": "Microsoft.Compute/virtualMachines",
        "metric_names": ["Percentage CPU", "Network In Total"]
    },
    {
        "type": "Microsoft.Sql/servers/databases",
        "namespace": "Microsoft.Sql/servers/databases",
        "metric_names": ["DTU Consumption Percent", "Deadlocks"]
    },
    {
        "type": "Microsoft.DocumentDB/databaseAccounts",
        "namespace": "Microsoft.DocumentDB/databaseAccounts",
        "metric_names": ["Total Requests", "Server Availability"]
    }
]

# Retrieve resource-level metric data
subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
resource_client = ResourceManagementClient(credential, subscription_id)
monitor_client = MonitorManagementClient(credential, subscription_id)

metric_data = []
for resource_type in resource_types:
    for metric_name in resource_type["metric_names"]:
        metric_response = monitor_client.metrics.list(
            resource_uri=f"/subscriptions/{subscription_id}/resourceGroups/your_resource_group/providers/{resource_type['type']}",
            timespan="P1Y",  # Replace with desired time range
            metric_names=[metric_name],
            namespace=resource_type["namespace"],
            result_type="data"
        )

        for metric in metric_response.value:
            for timeseries in metric.timeseries:
                for data in timeseries.data:
                    metric_data.append({
                        "resource_id": metric.resource.id,
                        "metric_name": metric.name.value,
                        "timestamp": data.time_stamp,
                        "value": data.average
                    })

# Convert metric data to a DataFrame
metric_df = pd.DataFrame(metric_data)
metric_df["timestamp"] = pd.to_datetime(metric_df["timestamp"])
metric_df.set_index("timestamp", inplace=True)

# Forecast using Seasonal ARIMA (SARIMA)
forecast_results = []
for resource_id, group in metric_df.groupby("resource_id"):
    for metric_name, data in group.groupby("metric_name"):
        model = auto_arima(data["value"], seasonal=True, trace=False)
        forecast = model.predict(n_periods=12)  # Forecast for the next 12 periods
        forecast_df = pd.DataFrame({"forecast": forecast}, index=pd.date_range(start=data.index[-1], periods=13, freq="M")[1:])
        forecast_results.append({"resource_id": resource_id, "metric_name": metric_name, "forecast": forecast_df})

# Print forecast results
for result in forecast_results:
    print(f"Resource ID: {result['resource_id']}")
    print(f"Metric Name: {result['metric_name']}")
    print(result["forecast"])
    print("\n")



Here's the updated Python code that includes forecasting using the Seasonal ARIMA (SARIMA) model and manages credentials securely:

```python
import os
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.monitor import MonitorManagementClient
import pandas as pd
from pmdarima import auto_arima
import warnings
warnings.filterwarnings("ignore")

# Azure AD application (client) ID
CLIENT_ID = os.environ["AZURE_CLIENT_ID"]

# Azure AD application (client) secret
CLIENT_SECRET = os.environ["AZURE_CLIENT_SECRET"]

# Azure AD tenant ID
TENANT_ID = os.environ["AZURE_TENANT_ID"]

# Authenticate with Azure AD
credential = ClientSecretCredential(
    tenant_id=TENANT_ID,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)

# Get an authenticated token for the resource
RESOURCE_URI = "https://management.azure.com/"
token = credential.get_token(RESOURCE_URI)
headers = {"Authorization": f"Bearer {token.token}"}

# Define resource types and metrics to forecast
resource_types = [
    {
        "type": "Microsoft.Compute/virtualMachines",
        "namespace": "Microsoft.Compute/virtualMachines",
        "metric_names": ["Percentage CPU", "Network In Total"]
    },
    {
        "type": "Microsoft.Sql/servers/databases",
        "namespace": "Microsoft.Sql/servers/databases",
        "metric_names": ["DTU Consumption Percent", "Deadlocks"]
    },
    {
        "type": "Microsoft.DocumentDB/databaseAccounts",
        "namespace": "Microsoft.DocumentDB/databaseAccounts",
        "metric_names": ["Total Requests", "Server Availability"]
    }
]

# Retrieve resource-level metric data
subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
resource_client = ResourceManagementClient(credential, subscription_id)
monitor_client = MonitorManagementClient(credential, subscription_id)

metric_data = []
for resource_type in resource_types:
    for metric_name in resource_type["metric_names"]:
        metric_response = monitor_client.metrics.list(
            resource_uri=f"/subscriptions/{subscription_id}/resourceGroups/your_resource_group/providers/{resource_type['type']}",
            timespan="P1Y",  # Replace with desired time range
            metric_names=[metric_name],
            namespace=resource_type["namespace"],
            result_type="data"
        )

        for metric in metric_response.value:
            for timeseries in metric.timeseries:
                for data in timeseries.data:
                    metric_data.append({
                        "resource_id": metric.resource.id,
                        "metric_name": metric.name.value,
                        "timestamp": data.time_stamp,
                        "value": data.average
                    })

# Convert metric data to a DataFrame
metric_df = pd.DataFrame(metric_data)
metric_df["timestamp"] = pd.to_datetime(metric_df["timestamp"])
metric_df.set_index("timestamp", inplace=True)

# Forecast using Seasonal ARIMA (SARIMA)
forecast_results = []
for resource_id, group in metric_df.groupby("resource_id"):
    for metric_name, data in group.groupby("metric_name"):
        model = auto_arima(data["value"], seasonal=True, trace=False)
        forecast = model.predict(n_periods=12)  # Forecast for the next 12 periods
        forecast_df = pd.DataFrame({"forecast": forecast}, index=pd.date_range(start=data.index[-1], periods=13, freq="M")[1:])
        forecast_results.append({"resource_id": resource_id, "metric_name": metric_name, "forecast": forecast_df})

# Print forecast results
for result in forecast_results:
    print(f"Resource ID: {result['resource_id']}")
    print(f"Metric Name: {result['metric_name']}")
    print(result["forecast"])
    print("\n")
```

Here are the key updates:

1. **Credential Management**: The code now uses the `ClientSecretCredential` from the `azure.identity` library to authenticate with Azure Active Directory (Azure AD). This approach requires setting the `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, and `AZURE_TENANT_ID` environment variables with your Azure AD application credentials. This is a more secure way of handling credentials compared to running as the current user.

2. **Metric Data Retrieval**: The code uses the `MonitorManagementClient` from the `azure.mgmt.monitor` library to retrieve metric data for the specified resource types and metric names. The retrieved metric data is stored in a list of dictionaries.

3. **Data Preparation**: The metric data is converted to a pandas DataFrame, and the timestamp is set as the index.

4. **Forecasting with SARIMA**: The code uses the `auto_arima` function from the `pmdarima` library to automatically select the best SARIMA model parameters and generate the forecast. The `seasonal=True` parameter is set to account for seasonality in the data. The forecast is generated for the next 12 periods (e.g., months).

5. **Forecast Results**: The forecast results are stored in a list of dictionaries, where each dictionary contains the resource ID, metric name, and the forecast DataFrame.

6. **Printing Forecast Results**: The forecast results are printed to the console, displaying the resource ID, metric name, and the forecast DataFrame.

Note that you need to install the required Python libraries (`pmdarima`, `azure-mgmt-monitor`, `azure-mgmt-resource`, and `azure-identity`) before running this code.

Additionally, you need to set the following environment variables with your Azure credentials and subscription ID:

- `AZURE_CLIENT_ID`: Azure AD application (client) ID
- `AZURE_CLIENT_SECRET`: Azure AD application (client) secret
- `AZURE_TENANT_ID`: Azure AD tenant ID
- `AZURE_SUBSCRIPTION_ID`: Azure subscription ID

Make sure to replace `"your_resource_group"` with the name of your resource group in the `monitor_client.metrics.list` call.

This code provides a more secure way of handling Azure credentials and incorporates the Seasonal ARIMA (SARIMA) model for forecasting resource usage based on historical metric data.
