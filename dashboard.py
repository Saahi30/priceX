import streamlit as st
import pandas as pd
import json
import subprocess
import os

st.set_page_config(page_title="Scraper Dashboard", layout="wide")

st.title("📈 Unlisted Shares Scraper Dashboard")

# Sidebar Configuration
st.sidebar.header("Scraper Configuration")
source = st.sidebar.selectbox("Source", ["all", "unlistedzone", "sharescart"])
mode = st.sidebar.selectbox("Mode", ["high-priority", "all"])

if st.sidebar.button("Run Scraper"):
    with st.spinner(f"Running scraper (Source: {source}, Mode: {mode})..."):
        try:
            # Run the scraper CLI and stream output
            log_container = st.empty()
            st.markdown("### 🔴 Live Data Feed")
            table_container = st.empty()
            
            process = subprocess.Popen(
                ["python", "-u", "-m", "scraper.main", "--mode", mode, "--source", source],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding="utf-8"
            )
            
            output_log = []
            live_data = []
            
            for line in iter(process.stdout.readline, ''):
                if line.startswith("LIVE_DATA:"):
                    try:
                        data = json.loads(line.replace("LIVE_DATA:", ""))
                        live_data.append(data)
                        df = pd.DataFrame(live_data)
                        # ensure columns are strictly ordered
                        if not df.empty:
                            df = df[["company", "price", "source"]]
                        table_container.dataframe(df, use_container_width=True)
                    except Exception as e:
                        pass
                else:
                    output_log.append(line)
                    # Keep only the last 15 lines of raw logs to avoid massive text block
                    log_container.code("".join(output_log[-15:]))
                
            process.stdout.close()
            return_code = process.wait()
            
            if return_code == 0:
                st.success("Scraping completed successfully!")
                with st.expander("View Full Terminal Logs"):
                    st.code("".join(output_log))
            else:
                st.error("Scraping failed!")
                with st.expander("View Error Logs"):
                    st.code("".join(output_log))
        except Exception as e:
            st.error(f"Execution failed: {e}")

# Display Data
st.subheader("Data Viewer")
data_file = "stocks_data.json"

if os.path.exists(data_file):
    with open(data_file, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            # data is a dictionary where keys are slugs
            df = pd.DataFrame.from_dict(data, orient='index')
            
            # Show high-level metrics
            col1, col2 = st.columns(2)
            col1.metric("Total Shares Tracked", len(df))
            
            sources = df['source'].value_counts() if 'source' in df.columns else {}
            source_stats = " | ".join([f"{k}: {v}" for k, v in sources.items()])
            col2.metric("Sources Breakdown", source_stats)
            
            # Display interactive dataframe
            st.dataframe(df, use_container_width=True)
            
            # Export to CSV
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv_data,
                file_name="scraped_stocks_data.csv",
                mime="text/csv",
            )
            
        except Exception as e:
            st.error(f"Error loading data: {e}")
else:
    st.info("No data found. Run the scraper to generate data.")
