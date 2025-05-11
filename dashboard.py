from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import sqlite3
import os


import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


# Get the absolute path to the database file
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inventory.db')

app = Flask(__name__)
app.secret_key = 'inventory'  # Change this to a random secret key

# Database connection function
def connect_db():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This allows us to use column names
    return conn

@app.route('/')
def dashboard():
    return render_template('dashboard.html')  # Main navigation


# Define a mapping of table names to their primary key column names
TABLE_PRIMARY_KEYS = {
    'history': 'serial',
    'weapons': 'weapon_id',
    'items': 'item_id',
    'technical_items': 'tech_item_id',
    # Add other tables and their primary key columns here
}

@app.route('/view/tables/<table_name>')
def view_table(table_name):
    conn = connect_db()
    cur = conn.cursor()
    
    # Fetch data from the specified table
    try:
        cur.execute(f"SELECT * FROM {table_name}")  # Use table_name parameter
        table_data = cur.fetchall()  # Fetch all records
        # Fetch column names
        column_names = [description[0] for description in cur.description]

    except sqlite3.Error as e:
        return f"An error occurred: {e}", 500
        
    finally:
        conn.close()

    # Render dashboard with the selected table data
    return render_template('dashboard.html', table_data=table_data, column_names=column_names, table_name=table_name)


# Route to insert record into a table
@app.route('/insert/<table_name>', methods=['POST'])
def insert_record(table_name):
    try:
        conn = connect_db()
        cur = conn.cursor()

        # Prepare SQL query for inserting data
        columns = request.form.keys()
        values = [request.form[column] for column in columns]
        placeholders = ', '.join(['?'] * len(values))
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        cur.execute(sql, values)
        conn.commit()
        flash(f'Record inserted into {table_name}', 'success')

    except sqlite3.IntegrityError as e:
        # Specific error for constraint violation, like UNIQUE constraint
        if "UNIQUE constraint failed" in str(e):
            flash(f'Error: A record with the same value already exists in {table_name}.', 'danger')
        else:
            flash(f'Integrity error inserting record: {e}', 'danger')

    except sqlite3.Error as e:
        # General SQLite error
        flash(f'Error inserting record: {e}', 'danger')

    finally:
        conn.close()

    return redirect(url_for('view_table', table_name=table_name))



# Route to delete record from a table
@app.route('/delete/<table_name>', methods=['POST'])
def delete_record(table_name):
    record_id = request.form['id']
    
    # Check if the table_name exists in the mapping
    if table_name not in TABLE_PRIMARY_KEYS:
        flash(f'Table "{table_name}" not found.', 'danger')
        return redirect(url_for('view_table', table_name=table_name))

    # Get the appropriate primary key column for the table
    primary_key_column = TABLE_PRIMARY_KEYS[table_name]

    try:
        conn = connect_db()
        cur = conn.cursor()

        # Prepare SQL query for deleting data using the dynamic column name
        sql = f"DELETE FROM {table_name} WHERE {primary_key_column} = ?"
        cur.execute(sql, (record_id,))
        if cur.rowcount == 0:
            flash(f'No record found with {primary_key_column} = {record_id}', 'danger')
        else:
            conn.commit()
            flash(f'Record with {primary_key_column} = {record_id} deleted from {table_name}', 'success')
        

    except sqlite3.Error as e:
        flash(f'Error deleting record: {e}', 'danger')

    finally:
        conn.close()

    return redirect(url_for('view_table', table_name=table_name))





# Route to update record in a table
@app.route('/update/<table_name>', methods=['POST'])
def update_record(table_name):
    if table_name not in TABLE_PRIMARY_KEYS:
        flash(f'Table "{table_name}" not found.', 'danger')
        return redirect(url_for('view_table', table_name=table_name))

    primary_key_column = TABLE_PRIMARY_KEYS[table_name]

    # Check if the primary key is present in the form data
    if primary_key_column not in request.form:
        flash(f'Missing {primary_key_column} in form data', 'danger')
        return redirect(url_for('view_table', table_name=table_name))

    record_id = request.form[primary_key_column]

    try:
        conn = connect_db()
        cur = conn.cursor()

        # Prepare SQL query for updating data
        columns = request.form.keys()
        updates = [f"{column} = ?" for column in columns if column != primary_key_column]
        values = [request.form[column] for column in columns if column != primary_key_column]

        sql = f"UPDATE {table_name} SET {', '.join(updates)} WHERE {primary_key_column} = ?"
        cur.execute(sql, values + [record_id])
        
        if cur.rowcount == 0:
            flash(f'No record found with {primary_key_column} = {record_id}', 'danger')
        else:
            conn.commit()
            flash(f'Record with {primary_key_column} = {record_id} updated in {table_name}', 'success')

    except sqlite3.Error as e:
        flash(f'Error updating record: {e}', 'danger')

    finally:
        conn.close()

    return redirect(url_for('view_table', table_name=table_name))

# Define a folder to save plots
output_folder = 'static'
os.makedirs(output_folder, exist_ok=True)

# Function to retrieve weapons data from the database
def get_weapons_data():
    # Connect to the SQLite database
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    # Execute the query to fetch weapon names and prices from the 'weapons' table
    cursor.execute("SELECT name, cost FROM weapons")
    rows = cursor.fetchall()
    
    # Close the database connection
    conn.close()
    
    # Return the data as a DataFrame
    return pd.DataFrame(rows, columns=['Weapon', 'Price'])

# Function to generate savings and plots
def generate_cost_savings_plots():
    # Create a dataframe from the database
    df = get_weapons_data()

    # Total inventory value
    total_inventory_value = df['Price'].sum()

    # Define savings percentages for each model
    savings_factors = {
        'Three-Statement Model (5%)': 0.05,
        'DCF Model (7%)': 0.07,
        'Comparable Company Analysis (3%)': 0.03,
        'Forecasting Model (2%)': 0.02,
        'Sum-of-the-Parts Model (4%)': 0.04,
        'Leveraged Buyout Model (5%)': 0.05,
        'Sensitivity Analysis (3%)': 0.03,
        'Economic Order Quantity (10%)': 0.10,
        'ABC Analysis (2%)': 0.02,
        'Activity-Based Costing (5%)': 0.05,
        'Just-In-Time Inventory Management (8%)': 0.08,
        'Cost Flow Assumptions (FIFO - 2%)': 0.02
    }

    # Apply the savings from each model
    savings = {}
    for model, percentage in savings_factors.items():
        savings[model] = total_inventory_value * percentage

    # Define the custom color palette
    custom_palette = ['#092C73', '#051940', '#F2CD88', '#F2E9D8', '#594031']

    # Function to save plots using Seaborn
    def plot_savings_bar_plot(savings):
        plt.figure(figsize=(14, 7))
        sns.barplot(x=list(savings.keys()), y=list(savings.values()), palette=custom_palette)
        plt.title('Cost Savings Per Model', fontsize=18)
        plt.ylabel('Savings (INR)', fontsize=14)
        plt.xticks(rotation=90, ha='right', fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, 'bar_plot.png'))  # Save the figure
        plt.close()

    def plot_savings_pie_chart(savings):
        plt.figure(figsize=(10, 10))
        plt.pie(savings.values(), labels=savings.keys(), autopct='%1.1f%%', startangle=140, colors=custom_palette)
        plt.title('Proportion of Savings Across Models', fontsize=18)
        plt.axis('equal')
        plt.savefig(os.path.join(output_folder, 'pie_chart.png'))  # Save the figure
        plt.close()

    def plot_cumulative_savings_line_plot(savings):
        plt.figure(figsize=(14, 7))
        cumulative_savings = np.cumsum(list(savings.values()))
        sns.lineplot(x=list(savings.keys()), y=cumulative_savings, marker='o', color='#092C73', linewidth=2)
        plt.title('Cumulative Savings Over Models', fontsize=18)
        plt.ylabel('Cumulative Savings (INR)', fontsize=14)
        plt.xticks(rotation=90, ha='right', fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, 'cumulative_savings.png'))  # Save the figure
        plt.close()

    def plot_savings_heatmap(savings):
        summary_df = pd.DataFrame({
            'Model': savings.keys(),
            'Savings (INR)': savings.values()
        })
        plt.figure(figsize=(12, 6))
        ax = sns.heatmap(summary_df.set_index('Model').T, annot=True, fmt='.2f', cmap=sns.color_palette(custom_palette, as_cmap=True), linewidths=0.5, annot_kws={"rotation": 90})
        plt.title('Savings Breakdown Heatmap', fontsize=18)
        plt.xlabel('Models', fontsize=14)
        plt.ylabel('Savings (INR)', fontsize=14)
        plt.xticks(rotation=45, ha='right', fontsize=12)
        plt.yticks(fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, 'heatmap.png'))  # Save the figure
        plt.close()

    # Generate and save all the plots
    plot_savings_bar_plot(savings)               # First plot: Bar plot
    plot_cumulative_savings_line_plot(savings)   # Second plot: Cumulative line plot
    plot_savings_pie_chart(savings)              # Third plot: Pie chart
    plot_savings_heatmap(savings)                # Fourth plot: Heatmap


@app.route('/cost_savings_analysis')
def cost_savings_analysis():
    return render_template('cost_savings_analysis')


@app.route('/')
def index():
    generate_cost_savings_plots()  # Generate plots when the dashboard is accessed
    return render_template('plots.html')  # Replace with your actual dashboard template name



# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
