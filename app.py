import streamlit as st
import pandas as pd

st.set_page_config(page_title="Worker Auto Allocation", layout="wide")

st.title("🏭 Smart Worker Allocation System")
st.write("Upload attendance and line requirements to auto-assign workers")

# Upload files
attendance_file = st.file_uploader(
    "Upload Attendance Excel (with Day sheets)",
    type=["xlsx"]
)

requirements_file = st.file_uploader(
    "Upload Production Line Requirements Excel",
    type=["xlsx"]
)

if attendance_file and requirements_file:

    attendance_xl = pd.ExcelFile(attendance_file)
    day = st.selectbox("Select Day", attendance_xl.sheet_names)

    attendance_df = attendance_xl.parse(day)
    requirements_df = pd.read_excel(requirements_file)

    st.subheader("📋 Attendance Preview")
    st.dataframe(attendance_df.head())

    st.subheader("⚙️ Line Requirements Preview")
    st.dataframe(requirements_df)

    if st.button("🚀 Auto Allocate Workers"):

        priority_map = {"High": 1, "Medium": 2, "Low": 3}
        requirements_df["Priority_Order"] = requirements_df["Priority"].map(priority_map)
        requirements_df = requirements_df.sort_values("Priority_Order")

        attendance_df["Assigned"] = False
        allocations = []

        for _, req in requirements_df.iterrows():
            skill = req["Skill"]
            needed = req["Required_Workers"]
            line = req["Production_Line"]

            eligible = attendance_df[
                (attendance_df["Skill"] == skill) &
                (attendance_df["Assigned"] == False)
            ]

            selected = eligible.head(needed)

            for _, worker in selected.iterrows():
                allocations.append({
                    "Worker_ID": worker["Worker_ID"],
                    "Name": worker["Name"],
                    "Skill": worker["Skill"],
                    "Skill_Level": worker["Skill_Level"],
                    "Production_Line": line
                })

            attendance_df.loc[selected.index, "Assigned"] = True

        allocation_df = pd.DataFrame(allocations)

        st.success("✅ Allocation Completed")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Present", len(attendance_df))
            st.metric("Allocated", len(allocation_df))
            st.metric("Unassigned", len(attendance_df) - len(allocation_df))

        with col2:
            st.write("📊 Allocation by Line")
            st.dataframe(
                allocation_df["Production_Line"].value_counts().reset_index()
                .rename(columns={"index": "Line", "Production_Line": "Workers"})
            )

        st.subheader("📤 Allocation Output")
        st.dataframe(allocation_df)

        # Download
        output_file = f"{day}_Auto_Allocation.xlsx"
        allocation_df.to_excel(output_file, index=False)

        with open(output_file, "rb") as file:
            st.download_button(
                label="⬇️ Download Allocation Excel",
                data=file,
                file_name=output_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.info("👆 Please upload both Excel files to proceed")
