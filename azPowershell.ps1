# Install the required modules
Install-Module -Name Az.Monitor -Scope CurrentUser
Install-Module -Name Az.Resources -Scope CurrentUser
Install-Module -Name TSUtils -Scope CurrentUser

# Connect to Azure
Connect-AzAccount

# Set the subscription ID
$subscriptionId = "your_subscription_id"
Set-AzContext -SubscriptionId $subscriptionId

# Define resource types and metrics to forecast
$resourceTypes = @(
    @{
        Type        = "Microsoft.Compute/virtualMachines"
        Namespace   = "Microsoft.Compute/virtualMachines"
        MetricNames = @("Percentage CPU", "Network In Total")
    },
    @{
        Type        = "Microsoft.Sql/servers/databases"
        Namespace   = "Microsoft.Sql/servers/databases"
        MetricNames = @("DTU Consumption Percent", "Deadlocks")
    },
    @{
        Type        = "Microsoft.DocumentDB/databaseAccounts"
        Namespace   = "Microsoft.DocumentDB/databaseAccounts"
        MetricNames = @("Total Requests", "Server Availability")
    }
)

# Define the forecast class
class ForecastItem {
    [DateTime] $Date
    [String] $ResourceType
    [String] $Resource
    [String] $Metric
    [Double] $Forecast
}

# Retrieve resource-level metric data for each resource type and metric
$resourceGroupName = "your_resource_group"
$startTime = (Get-Date).AddYears(-2)  # Increase the time range for better model training
$endTime = Get-Date
$allMetrics = foreach ($resourceType in $resourceTypes) {
    foreach ($metricName in $resourceType.MetricNames) {
        Get-AzMetric -ResourceGroupName $resourceGroupName -ResourceType $resourceType.Type -MetricNamespace $resourceType.Namespace -MetricName $metricName -StartTime $startTime -EndTime $endTime
    }
}

# Convert metric data to a data table
$metricsTable = foreach ($metrics in $allMetrics) {
    $metrics | Select-Object -Property @{Name = "ResourceType"; Expression = { $resourceType.Type } }, `
                                        @{Name = "Resource"; Expression = { $_.ResourceId.Split('/') | Select-Object -Last 1 } }, `
                                        @{Name = "Metric"; Expression = { $_.Name.Value } }, `
                                        @{Name = "Date"; Expression = { $_.Data.TimeStamp } }, `
                                        @{Name = "Value"; Expression = { $_.Data.Average } }
}

# Forecast using Seasonal ARIMA (SARIMA)
$forecast = foreach ($resource in ($metricsTable | Select-Object -ExpandProperty Resource -Unique)) {
    foreach ($metric in ($metricsTable | Where-Object { $_.Resource -eq $resource } | Select-Object -ExpandProperty Metric -Unique)) {
        $data = $metricsTable | Where-Object { $_.Resource -eq $resource -and $_.Metric -eq $metric } | Select-Object Date, Value
        $ts = New-TsObject -Data $data -TimeStamp Date -Value Value -Frequency 12  # Assuming monthly data
        $model = SARIMA-Model -ts $ts
        $forecastResult = SARIMA-Forecast -model $model -Periods 12  # Forecast for the next 12 months

        foreach ($row in $forecastResult) {
            [ForecastItem]@{
                Date         = $row.TimeStamp
                ResourceType = $resourceType.Type
                Resource     = $resource
                Metric       = $metric
                Forecast     = $row.Forecast
            }
        }
    }
}

# Print the forecast
$forecast | Format-Table
