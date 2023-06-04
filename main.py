import altair as alt
import pandas as pd
import streamlit as st

st.write("# Budget")

conn = st.experimental_connection('budget_db', type='sql')
expenses = conn.query('select e.date, e.amount, e.description, c.name, c.is_fixed_cost '
                      'from expenses e '
                      'join categories c on c.id = e.category_id').assign(
    date=lambda x: pd.to_datetime(x.date, ))

include_fixed_costs = st.sidebar.checkbox('Include Fixed Costs')


if not include_fixed_costs:
    expenses = expenses[expenses.is_fixed_cost == 0]

selected_category = st.sidebar.multiselect("Category", expenses.name.unique())
selected_expenses = expenses[expenses.name.isin(selected_category)]

monthly_expenses = (selected_expenses
                    .set_index('date')
                    .groupby('name')
                    .resample('MS')['amount']
                    .sum()
                    .mul(-1))


st.dataframe(monthly_expenses.unstack('name').fillna(0))

avg_monthly_expenses = (
    monthly_expenses.reset_index().groupby('name')['amount'].mean().round(0).sort_values()
)

monthly_expenses.unstack("name").fillna(0).to_csv('monthly_expenses.csv')

st.dataframe(avg_monthly_expenses)

st.altair_chart(
    alt.Chart(monthly_expenses.reset_index())
    .mark_bar()
    .encode(x=alt.X('date:T').title('Date'),
            y=alt.Y('amount:Q').title('Total'),
            facet=alt.Facet('name:O').columns(2).title('Category')))
