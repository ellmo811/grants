import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="OakNorth Grants Working Sheet", layout="wide")

st.title("OakNorth Grants Working Sheet")

# Initialize time period (years 0-10)
years = list(range(0, 11))

# Define the sidebar inputs
st.sidebar.header("Input Parameters")

# PBT Growth Rate (at the top)
pbt_growth_rate = st.sidebar.slider(
    "PBT Growth Rate (%)", 
    min_value=0.0, 
    max_value=20.0, 
    value=15.0, 
    step=1.0,
    help="Year-over-year growth rate of share price"
) / 100.0  # Convert to decimal

# Common Share Section
st.sidebar.markdown("## Common Share")

common_redemption_percentage = st.sidebar.slider(
    "Common Share Redemption (%)", 
    min_value=0.0, 
    max_value=10.0, 
    value=5.0, 
    step=1.0,
    help="Percentage of common shares to redeem each year"
) / 100.0  # Convert to decimal

total_common_shares = st.sidebar.number_input(
    "Total Common Shares", 
    min_value=1, 
    value=10000, 
    step=100,
    help="Total number of common shares granted"
)

common_purchase_price = st.sidebar.number_input(
    "Common Share Purchase Price ($)", 
    min_value=0.01, 
    value=1.00, 
    step=0.01,
    help="Price at which common shares were purchased"
)

# A-Share / Options Section
st.sidebar.markdown("## A-Share / Options")

options_redemption_percentage = st.sidebar.slider(
    "A-Share/Options Redemption (%)", 
    min_value=0.0, 
    max_value=10.0, 
    value=5.0, 
    step=1.0,
    help="Percentage of vested unsold options to redeem each year"
) / 100.0  # Convert to decimal

strike_price = st.sidebar.number_input(
    "Strike Price ($)", 
    min_value=0.01, 
    value=10.00, 
    step=0.01,
    help="Price at which options can be exercised"
)

total_grant_shares = st.sidebar.number_input(
    "Total Grant Shares", 
    min_value=1, 
    value=10000, 
    step=100,
    help="Total number of option shares granted"
)

# Vesting schedule
st.sidebar.caption("Vesting Schedule (cumulative % of total shares)")
vesting_schedule = {}
for year in range(1, 11):
    default_value = min(25.0 * year, 100.0)  # Default 25% vest per year for first 4 years, then 100%
    vesting_schedule[year] = st.sidebar.number_input(
        f"Year {year} Vesting (%)", 
        min_value=0.0, 
        max_value=100.0, 
        value=default_value, 
        step=1.0,
        key=f"vest_{year}"
    ) / 100.0  # Convert to decimal

# Add option to start redemption in year 2
start_redemption_year = st.sidebar.selectbox(
    "Start Redemption in Year",
    options=[1, 2, 3],
    index=1,  # Default to year 2
    help="Year to start redeeming shares"
)

# Calculate Common Share values
def calculate_common_share_values():
    # Initialize arrays
    share_price = [0] * 11
    share_price[0] = common_purchase_price  # Initial share price at year 0
    
    unsold_shares = [0] * 11
    unsold_shares[0] = total_common_shares  # All shares are unsold at year 0
    
    redeemed_shares = [0] * 11
    cumulative_redeemed_shares = [0] * 11
    
    redemption_value = [0] * 11
    cumulative_redemption_value = [0] * 11
    
    value_of_unsold_shares = [0] * 11
    total_grant_value = [0] * 11
    
    # Year 0 calculations
    value_of_unsold_shares[0] = 0  # No value above purchase price in year 0
    
    # Calculate for years 1-10
    for year in range(1, 11):
        # Share price calculation
        share_price[year] = share_price[year-1] * (1 + pbt_growth_rate)
        
        # No redemption before start year
        if year < start_redemption_year:
            redeemed_shares[year] = 0
        else:
            # Redeemed shares
            redeemed_shares[year] = unsold_shares[year-1] * common_redemption_percentage
        
        # Update cumulative redeemed shares
        cumulative_redeemed_shares[year] = cumulative_redeemed_shares[year-1] + redeemed_shares[year]
        
        # Unsold shares
        unsold_shares[year] = total_common_shares - cumulative_redeemed_shares[year]
        
        # Redemption value
        redemption_value[year] = max(0, (share_price[year] - common_purchase_price)) * redeemed_shares[year]
        
        # Update cumulative redemption value
        cumulative_redemption_value[year] = cumulative_redemption_value[year-1] + redemption_value[year]
        
        # Value of unsold shares
        value_of_unsold_shares[year] = max(0, (share_price[year] - common_purchase_price)) * unsold_shares[year]
        
        # Total grant value
        total_grant_value[year] = cumulative_redemption_value[year] + value_of_unsold_shares[year]
    
    # Create DataFrame for display
    df = pd.DataFrame(index=range(0, 11))
    df["Year"] = range(0, 11)
    df["Share Price ($)"] = share_price
    df["Redeemed Shares"] = redeemed_shares
    df["Cumulative Redeemed Shares"] = cumulative_redeemed_shares
    df["Unsold Shares"] = unsold_shares
    df["Redemption Value ($)"] = redemption_value
    df["Cumulative Redemption Value ($)"] = cumulative_redemption_value
    df["Value of Unsold Shares ($)"] = value_of_unsold_shares
    df["Total Grant Value ($)"] = total_grant_value
    
    # Set Year as index
    df = df.set_index("Year")
    
    return df

# Calculate Option values
def calculate_option_values():
    # Initialize arrays
    share_price = [0] * 11
    share_price[0] = strike_price  # Initial share price at year 0 is strike price
    
    vested_shares = [0] * 11
    vested_shares[0] = 0  # No vested shares at year 0
    
    redeemed_shares = [0] * 11
    cumulative_redeemed_shares = [0] * 11
    
    unsold_shares = [0] * 11
    unsold_shares[0] = total_grant_shares  # All shares are unsold at year 0
    
    redemption_value = [0] * 11
    cumulative_redemption_value = [0] * 11
    
    value_of_unsold_shares = [0] * 11
    total_grant_value = [0] * 11
    
    # Calculate for years 1-10
    for year in range(1, 11):
        # Share price calculation
        share_price[year] = share_price[year-1] * (1 + pbt_growth_rate)
        
        # Vested shares (cumulative)
        vested_shares[year] = total_grant_shares * vesting_schedule[year]
        
        # No redemption before start year
        if year < start_redemption_year:
            redeemed_shares[year] = 0
        else:
            # Redeemed shares
            unvested_shares_prev_year = unsold_shares[year-1]
            redeemed_shares[year] = unvested_shares_prev_year * options_redemption_percentage
        
        # Update cumulative redeemed shares
        cumulative_redeemed_shares[year] = cumulative_redeemed_shares[year-1] + redeemed_shares[year]
        
        # Unsold shares
        unsold_shares[year] = total_grant_shares - cumulative_redeemed_shares[year]
        
        # Redemption value
        redemption_value[year] = max(0, (share_price[year] - strike_price)) * redeemed_shares[year]
        
        # Update cumulative redemption value
        cumulative_redemption_value[year] = cumulative_redemption_value[year-1] + redemption_value[year]
        
        # Value of unsold shares
        value_of_unsold_shares[year] = max(0, (share_price[year] - strike_price)) * unsold_shares[year]
        
        # Total grant value
        total_grant_value[year] = cumulative_redemption_value[year] + value_of_unsold_shares[year]
    
    # Create DataFrame for display
    df = pd.DataFrame(index=range(0, 11))
    df["Year"] = range(0, 11)
    df["Share Price ($)"] = share_price
    df["Vested Shares"] = vested_shares
    df["Redeemed Shares"] = redeemed_shares
    df["Cumulative Redeemed Shares"] = cumulative_redeemed_shares
    df["Unsold Shares"] = unsold_shares
    df["Redemption Value ($)"] = redemption_value
    df["Cumulative Redemption Value ($)"] = cumulative_redemption_value
    df["Value of Unsold Shares ($)"] = value_of_unsold_shares
    df["Total Grant Value ($)"] = total_grant_value
    
    # Set Year as index
    df = df.set_index("Year")
    
    return df

# Calculate combined grant values
def calculate_combined_values(common_df, options_df):
    combined_df = pd.DataFrame(index=range(0, 11))
    combined_df["Year"] = range(0, 11)
    combined_df["Common Share Value ($)"] = common_df["Total Grant Value ($)"]
    combined_df["A-Share/Options Value ($)"] = options_df["Total Grant Value ($)"]
    combined_df["Combined Total Value ($)"] = combined_df["Common Share Value ($)"] + combined_df["A-Share/Options Value ($)"]
    combined_df = combined_df.set_index("Year")
    return combined_df

# Calculate results
common_results = calculate_common_share_values()
options_results = calculate_option_values()
combined_results = calculate_combined_values(common_results, options_results)

# Format for display
def format_dataframe(df):
    formatted_df = df.copy()
    for col in formatted_df.columns:
        if "Value" in col or "Price" in col:
            formatted_df[col] = formatted_df[col].map('${:,.2f}'.format)
        elif "Shares" in col:
            formatted_df[col] = formatted_df[col].map('{:,.0f}'.format)
    return formatted_df

formatted_common = format_dataframe(common_results)
formatted_options = format_dataframe(options_results)
formatted_combined = format_dataframe(combined_results)

# Display Common Share results
st.header("Common Share Grant Value")
st.dataframe(formatted_common[["Share Price ($)", "Redeemed Shares", "Redemption Value ($)", 
                             "Cumulative Redemption Value ($)", "Unsold Shares", 
                             "Value of Unsold Shares ($)", "Total Grant Value ($)"]], 
             use_container_width=True)

# Display Option results
st.header("A-Share / Options Grant Value")
st.dataframe(formatted_options[["Share Price ($)", "Vested Shares", "Redeemed Shares", 
                              "Redemption Value ($)", "Cumulative Redemption Value ($)", 
                              "Unsold Shares", "Value of Unsold Shares ($)", "Total Grant Value ($)"]], 
             use_container_width=True)

# Display Combined results
st.header("Combined Grants Value")
st.dataframe(formatted_combined, use_container_width=True)

# Visualizations section
st.header("Grant Value Visualizations")

# Create visualization tabs
tab1, tab2, tab3 = st.tabs(["Common Share Value", "A-Share/Options Value", "Combined Value"])

# Function to calculate values at different redemption rates
def calculate_at_different_rates(pbt=0.15, redemption_rates=[0.00, 0.05, 0.10]):
    common_values = []
    option_values = []
    
    for rate in redemption_rates:
        # Calculate common share values with this rate
        temp_common = calculate_common_share_values_for_viz(rate, pbt)
        common_values.append(temp_common["Total Grant Value ($)"].iloc[1:10])  # Years 1-9
        
        # Calculate option values with this rate
        temp_option = calculate_option_values_for_viz(rate, pbt)
        option_values.append(temp_option["Total Grant Value ($)"].iloc[1:10])  # Years 1-9
    
    return common_values, option_values

def calculate_common_share_values_for_viz(redemption_rate, pbt_rate):
    # Modified version of calculate_common_share_values for visualization
    # Similar code but using the passed parameters instead of globals
    # Initialize arrays
    share_price = [0] * 11
    share_price[0] = common_purchase_price
    
    unsold_shares = [0] * 11
    unsold_shares[0] = total_common_shares
    
    redeemed_shares = [0] * 11
    cumulative_redeemed_shares = [0] * 11
    
    redemption_value = [0] * 11
    cumulative_redemption_value = [0] * 11
    
    value_of_unsold_shares = [0] * 11
    total_grant_value = [0] * 11
    
    for year in range(1, 11):
        share_price[year] = share_price[year-1] * (1 + pbt_rate)
        
        if year < start_redemption_year:
            redeemed_shares[year] = 0
        else:
            redeemed_shares[year] = unsold_shares[year-1] * redemption_rate
        
        cumulative_redeemed_shares[year] = cumulative_redeemed_shares[year-1] + redeemed_shares[year]
        unsold_shares[year] = total_common_shares - cumulative_redeemed_shares[year]
        redemption_value[year] = max(0, (share_price[year] - common_purchase_price)) * redeemed_shares[year]
        cumulative_redemption_value[year] = cumulative_redemption_value[year-1] + redemption_value[year]
        value_of_unsold_shares[year] = max(0, (share_price[year] - common_purchase_price)) * unsold_shares[year]
        total_grant_value[year] = cumulative_redemption_value[year] + value_of_unsold_shares[year]
    
    df = pd.DataFrame(index=range(0, 11))
    df["Year"] = range(0, 11)
    df["Total Grant Value ($)"] = total_grant_value
    df = df.set_index("Year")
    
    return df

def calculate_option_values_for_viz(redemption_rate, pbt_rate):
    # Modified version of calculate_option_values for visualization
    # Similar code but using the passed parameters instead of globals
    share_price = [0] * 11
    share_price[0] = strike_price
    
    vested_shares = [0] * 11
    vested_shares[0] = 0
    
    redeemed_shares = [0] * 11
    cumulative_redeemed_shares = [0] * 11
    
    unsold_shares = [0] * 11
    unsold_shares[0] = total_grant_shares
    
    redemption_value = [0] * 11
    cumulative_redemption_value = [0] * 11
    
    value_of_unsold_shares = [0] * 11
    total_grant_value = [0] * 11
    
    for year in range(1, 11):
        share_price[year] = share_price[year-1] * (1 + pbt_rate)
        vested_shares[year] = total_grant_shares * vesting_schedule[year]
        
        if year < start_redemption_year:
            redeemed_shares[year] = 0
        else:
            unvested_shares_prev_year = unsold_shares[year-1]
            redeemed_shares[year] = unvested_shares_prev_year * redemption_rate
        
        cumulative_redeemed_shares[year] = cumulative_redeemed_shares[year-1] + redeemed_shares[year]
        unsold_shares[year] = total_grant_shares - cumulative_redeemed_shares[year]
        redemption_value[year] = max(0, (share_price[year] - strike_price)) * redeemed_shares[year]
        cumulative_redemption_value[year] = cumulative_redemption_value[year-1] + redemption_value[year]
        value_of_unsold_shares[year] = max(0, (share_price[year] - strike_price)) * unsold_shares[year]
        total_grant_value[year] = cumulative_redemption_value[year] + value_of_unsold_shares[year]
    
    df = pd.DataFrame(index=range(0, 11))
    df["Year"] = range(0, 11)
    df["Total Grant Value ($)"] = total_grant_value
    df = df.set_index("Year")
    
    return df

# Calculate values for different redemption rates
redemption_rates = [0.00, 0.05, 0.10]
rate_labels = ["0% Redemption", "5% Redemption", "10% Redemption"]
common_values, option_values = calculate_at_different_rates(pbt_growth_rate, redemption_rates)

# Common Share Value tab
with tab1:
    st.subheader("Common Share Grant Value at Various Redemption Rates")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, rate in enumerate(redemption_rates):
        ax.plot(range(1, 10), common_values[i], marker='o', label=f"{int(rate*100)}% Redemption")
    
    ax.set_xlabel('Year')
    ax.set_ylabel('Total Grant Value ($)')
    ax.set_title('Common Share Grant Value Over Time')
    ax.legend()
    ax.grid(True)
    
    st.pyplot(fig)

# A-Share/Options Value tab
with tab2:
    st.subheader("A-Share/Options Grant Value at Various Redemption Rates")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, rate in enumerate(redemption_rates):
        ax.plot(range(1, 10), option_values[i], marker='o', label=f"{int(rate*100)}% Redemption")
    
    ax.set_xlabel('Year')
    ax.set_ylabel('Total Grant Value ($)')
    ax.set_title('A-Share/Options Grant Value Over Time')
    ax.legend()
    ax.grid(True)
    
    st.pyplot(fig)

# Combined Value tab
with tab3:
    st.subheader("Combined Grant Value at Different PBT Growth Rates")
    
    # Calculate combined values for different PBT rates with 0% redemption
    pbt_rates = [0.15, 0.20]  # 15% and 20%
    pbt_labels = ["15% PBT Growth", "20% PBT Growth"]
    
    combined_values_by_pbt = []
    
    for pbt_rate in pbt_rates:
        common_at_pbt = calculate_common_share_values_for_viz(0, pbt_rate)  # 0% redemption
        option_at_pbt = calculate_option_values_for_viz(0, pbt_rate)  # 0% redemption
        
        # Combined value
        combined_value = common_at_pbt["Total Grant Value ($)"] + option_at_pbt["Total Grant Value ($)"]
        combined_values_by_pbt.append(combined_value.iloc[1:10])  # Years 1-9
    
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, pbt_rate in enumerate(pbt_rates):
        ax.plot(range(1, 10), combined_values_by_pbt[i], marker='o', label=f"{int(pbt_rate*100)}% PBT Growth")
    
    ax.set_xlabel('Year')
    ax.set_ylabel('Combined Grant Value ($)')
    ax.set_title('Combined Grant Value with No Share Redemption')
    ax.legend()
    ax.grid(True)
    
    st.pyplot(fig)

# Download button
st.header("Download Results")
csv_common = common_results.to_csv().encode('utf-8')
csv_options = options_results.to_csv().encode('utf-8')
csv_combined = combined_results.to_csv().encode('utf-8')

col1, col2, col3 = st.columns(3)
with col1:
    st.download_button(
        label="Download Common Share Data",
        data=csv_common,
        file_name="common_share_values.csv",
        mime="text/csv",
    )
with col2:
    st.download_button(
        label="Download A-Share/Options Data",
        data=csv_options,
        file_name="options_values.csv",
        mime="text/csv",
    )
with col3:
    st.download_button(
        label="Download Combined Data",
        data=csv_combined,
        file_name="combined_values.csv",
        mime="text/csv",
    )
