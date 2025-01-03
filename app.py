import streamlit as st
import pandas as pd
import json
import plotly.express as px
from essentials import RobotPathVisualizer

def main(): 
    st.set_page_config(layout="wide")
    st.title("Test Case Report")

    # File uploader
    uploaded_file = st.sidebar.file_uploader("Upload LOG file", type=['json'])
    # local_file = r"C:\mac\aug\QA_dashboard\test_logs\test_log_file.json"  

    if uploaded_file is not None:
        try:
            json_data = uploaded_file.read()
            if json_data:
                # If the content is not empty, try loading the JSON
                json_data = json.loads(json_data)
                st.sidebar.success("JSON file loaded successfully!")
                # Convert JSON data to DataFrame
                df = pd.DataFrame(json_data)
                df['startdate'] = pd.to_datetime(df['startdate'])
                df['date'] = df['startdate'].dt.date
                df['status'] = df['test_status'].apply(lambda x: 'Failed' if 'FAIL' in x else 'Passed')
                df['category'] = df['testname'].apply(lambda x: x.split(' ')[0] if x else 'Unknown')
                
                # Add failure type classification
                def get_failure_type(test_status):
                    if 'FAIL' not in test_status:
                        return None
                    elif 'Files have unequal lengths' in test_status:
                        return 'Files have unequal lengths'
                    else:
                        return 'Fail due to threshold'
                
                df['failure_type'] = df['test_status'].apply(get_failure_type)
                
                # Filters
                st.sidebar.header("Filters")
                dates = sorted(df['date'].unique())
                # selected_dates = st.sidebar.multiselect("Select Dates", dates, default=dates)
                selected_dates = st.sidebar.selectbox("Select Date", dates, index=0)  # Changed to single select

                selected_status = st.sidebar.radio("Select Status to View Tests", ['Home', 'Passed', 'Failed'])
                
                # Add failure type filter when Failed is selected
                selected_failure_types = None
                if selected_status == 'Failed':
                    failure_types = ['Files have unequal lengths', 'Fail due to threshold']
                    selected_failure_types = st.sidebar.multiselect(
                        "Select Failure Types",
                        failure_types,
                        default=failure_types
                    )
                
                # Filter data
                filtered_df = df[df['date'] == selected_dates] 
                # filtered_df = df[df['date'].isin(selected_dates)]
                if selected_status != 'Home':
                    filtered_df = filtered_df[filtered_df['status'] == selected_status]
                    if selected_status == 'Failed' and selected_failure_types:
                        filtered_df = filtered_df[filtered_df['failure_type'].isin(selected_failure_types)]

                        if filtered_df.empty:
                            # Display the message in green color under the 'selected_failure_types' content
                            st.sidebar.markdown(f'<p style="color:green;">No error with: {str(selected_failure_types[0])}</p>', unsafe_allow_html=True)
                        
                
                if selected_status != 'Home' and not filtered_df.empty:
                    available_categories = filtered_df['category'].unique()
                    selected_category = st.sidebar.selectbox("Select Category to View", available_categories)
                    filtered_category_df = filtered_df[filtered_df['category'] == selected_category]
                    
                    if not filtered_category_df.empty:
                        selected_test = st.sidebar.selectbox(
                            "Select Test to View Details", 
                            filtered_category_df['testname'].tolist()
                        )
                        
                        if selected_test:
                            test_case = filtered_category_df[
                                filtered_category_df['testname'] == selected_test
                            ].iloc[0].to_dict()
                            
                            # Check if test failed due to unequal lengths
                            is_unequal_length_fail = test_case['test_status'] == "\u274c FAIL: Files have unequal lengths."
                            
                            # Display test details in two columns
                            st.header("Test Details")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Test Name:** {test_case['testname']}")
                                st.write(f"**Test Date:** {test_case['startdate']}")
                                st.write(f"**Status:** {test_case['test_status']}")
                            
                            # Only show analysis if not an unequal length failure
                            if not is_unequal_length_fail:
                                try:
                                    PathVisualizer = RobotPathVisualizer(test_case)
                                    insights = PathVisualizer.generate_insights_report()

                                    deviations_data = {
                                        'Axis': ['X', 'Y', 'Z'],
                                        'Max Deviations (mm)': [insights['max_deviation']['x'], 
                                                                insights['max_deviation']['y'], 
                                                                insights['max_deviation']['z']],
                                        'Mean Deviations (mm)': [insights['mean_deviation']['x'], 
                                                                insights['mean_deviation']['y'], 
                                                                insights['mean_deviation']['z']]
                                    }

                                    df_deviations = pd.DataFrame(deviations_data)

                                    # Convert DataFrame to HTML table with custom CSS
                                    html_table = df_deviations.to_html(index=False, escape=False)

                                    # Custom CSS for table alignment
                                    table_style = """
                                        <style>
                                            table {
                                                width: 100%;
                                                text-align: center;
                                                margin-left: auto;
                                                margin-right: auto;
                                            }
                                            th, td {
                                                padding: 8px;
                                                text-align: center;
                                            }
                                        </style>
                                    """
                                                                                        
                                    with col2:
                                        st.write("**Deviation Insights**")
                                        st.markdown(table_style, unsafe_allow_html=True)
                                        st.markdown(html_table, unsafe_allow_html=True)

                                    st.header("Visualization")
                                    st.plotly_chart(PathVisualizer.plot_3d_paths(), use_container_width=True)
                                    st.plotly_chart(PathVisualizer.plot_deviation_analysis(), use_container_width=True)

                                except Exception as e:
                                    st.error(f"Error generating visualizations: {str(e)}")
                            
                            # Display scripts at the bottom
                            st.header("Test Scripts")
                            col_scripts1, col_scripts2 = st.columns(2)
                            col_scripts3, col_scripts4 = st.columns(2)
                            
                            with col_scripts1:
                                master_script = test_case.get('master_script', 'No master script found')
                                st.write("**Master Script:**")
                                st.code(master_script, language='python')
                            
                            with col_scripts2:
                                test_script = test_case.get('test_script', 'No test script found')
                                st.write("**Test Script:**")
                                st.code(test_script, language='python')

                            # Get the 'diff_or_unequal_length_info' from test_case
                            diff_info = test_case.get('unequal_length_info', {})

                            if diff_info:
                                extra_master_script = diff_info.get('extra_lines_in_file1', [])
                                extra_test_script = diff_info.get('extra_lines_in_file2', [])
                                formatted_master_script = "\n".join(extra_master_script) if extra_master_script else 'No extra lines found in Master Script.'
                                formatted_test_script = "\n".join(extra_test_script) if extra_test_script else 'No extra lines found in Test Script.'

                                with st.expander("Extra lines in scripts", expanded=False):
                                    col_scripts3, col_scripts4 = st.columns(2)

                                    with col_scripts3:
                                        st.write("**Extra lines on Master Script:**")
                                        st.code(formatted_master_script, language='python')

                                    with col_scripts4:
                                        st.write("**Extra lines on Test Script:**")
                                        st.code(formatted_test_script, language='python')
                            else:
                                st.write("**Scripts are in same length**")
                            
                else:
                    col1, col2 = st.columns([4, 6])
                    
                    with col1:
                        status_counts = filtered_df['status'].value_counts()
                        total_count = len(filtered_df)
                        
                        fig_pie = px.pie(
                            values=status_counts.values,
                            names=status_counts.index,
                            color=status_counts.index,
                            title='Test Results Distribution',
                            color_discrete_map={'Passed': '#90EE90', 'Failed': '#FFB6C1'},
                            hole=0.3
                        )

                        fig_pie.update_traces(textinfo='label+value',pull=[0.05, 0.05])
                        fig_pie.update_layout(
                            showlegend=True,
                            annotations=[{
                                'text': f'Total: {total_count}',
                                'x': 0.5, 'y': 0.5,
                                'font_size': 15,
                                'showarrow': False
                            }]
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with col2:
                        category_status = filtered_df.groupby(['category', 'status']).size().reset_index(name='count')
                        fig_bar = px.bar(
                            category_status,
                            x='category',
                            y='count',
                            color='status',
                            labels={'category': 'Test Category', 'count': 'Number of Tests'},
                            title='Test Category Distribution by Status',
                            color_discrete_map={'Passed': '#90EE90', 'Failed': '#FFB6C1'},
                            barmode='stack'
                        )
                        fig_bar.update_layout(bargap=0.2)
                        st.plotly_chart(fig_bar, use_container_width=True)
                        
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')

                    if df['date'].isnull().any():
                        st.warning("Some date values could not be converted properly.")

                    trend_data = df.groupby(['date', 'status']).size().reset_index(name='count')

                    fig_trend = px.line(
                        trend_data,
                        x='date',
                        y='count',
                        color='status',
                        color_discrete_map={'Passed': '#90EE90', 'Failed': '#FFB6C1'},
                        markers=True,
                        line_shape='linear'
                    )

                    fig_trend.update_layout(
                        yaxis_title='Number of Tests',
                        xaxis_title='Date',
                        xaxis=dict(
                            tickformat="%d-%m-%Y",
                            tickmode='array',
                        )
                    )

                    st.header("Trend of Test Results")
                    st.plotly_chart(fig_trend, use_container_width=True)
                
     
            else:
                st.sidebar.error("The uploaded JSON file is empty!")
        
        except json.JSONDecodeError:
            # Handle cases where the file isn't a valid JSON file
            st.sidebar.error("Invalid JSON file. Please upload a valid JSON file.")
        except Exception as e:
            # Catch any other unexpected errors
            st.sidebar.error(f"An error occurred: {str(e)}")
        
        

if __name__ == "__main__":
    main()
