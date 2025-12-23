import streamlit as st
import pandas as pd

st.set_page_config(page_title="Worker Auto Allocation", layout="wide")

st.title("🏭 Smart Worker Allocation System")
st.write("Upload attendance and line requirements to auto-assign workers")

attendance_file = st.file_uploader(
    "Upload Attendance Excel (with Day sheets)",
    type=["xlsx"]
)

requirements_file = st.file_uploader(
    "Upload Production Line Requirements Excel",
    type=["xlsx"]
)

if attendance_file and requirements_file:

    attendance_xl = pd.ExcelFile(attendance_file, engine="openpyxl")
    day = st.selectbox("Select Day", attendance_xl.sheet_names)

    attendance_df = attendance_xl.parse(day)
    requirements_df = pd.read_excel(requirements_file, engine="openpyxl")

    st.subheader("📋 Attendance Preview")
    st.dataframe(attendance_df.head())

    st.subheader("⚙️ Line Requirements Preview")
    st.dataframe(requirements_df)

    if st.button("🚀 Auto Allocate Workers"):

        # ---- PRIORITY SORTING ----
        priority_map = {"High": 1, "Medium": 2, "Low": 3}
        requirements_df["Priority_Order"] = requirements_df["Priority"].map(priority_map)
        requirements_df = requirements_df.sort_values("Priority_Order")

        # ---- INITIALIZE ----
        attendance_df["Assigned"] = False
        allocations = []
        shortfall = []

        available_workers = len(attendance_df)

        # ---- ALLOCATION LOOP ----
        for _, req in requirements_df.iterrows():

            skill = req["Skill"]
            required = req["Required_Workers"]
            line = req["Production_Line"]
            priority = req["Priority"]

            if available_workers <= 0:
                shortfall.append({
                    "Production_Line": line,
                    "Skill": skill,
                    "Required": required,
                    "Allocated": 0,
                    "Shortfall": required
                })
                continue

            eligible = attendance_df[
                (attendance_df["Skill"] == skill) &
                (attendance_df["Assigned"] == False)
            ]

            allocated_count = min(len(eligible), required)
            selected = eligible.head(allocated_count)

            for _, worker in selected.iterrows():
                allocations.append({
                    "Worker_ID": worker["Worker_ID"],
                    "Name": worker["Name"],
                    "Skill": worker["Skill"],
                    "Skill_Level": worker["Skill_Level"],
                    "Production_Line": line,
                    "Priority": priority
                })

            attendance_df.loc[selected.index, "Assigned"] = True
            available_workers -= allocated_count

            if allocated_count < required:
                shortfall.append({
                    "Production_Line": line,
                    "Skill": skill,
                    "Required": required,
                    "Allocated": allocated_count,
                    "Shortfall": required - allocated_count
                })

        # ---- OUTPUT DATA ----
        allocation_df = pd.DataFrame(allocations)
        shortfall_df = pd.DataFrame(shortfall)

        st.success("✅ Allocation Completed")

        # ---- METRICS ----
        st.subheader("📈 Daily Manpower Summary")
        st.metric("Workers Present", len(attendance_df))
        st.metric("Total Requirement", requirements_df["Required_Workers"].sum())
        st.metric("Total Allocated", len(allocation_df))
        st.metric("Total Shortfall", shortfall_df["Shortfall"].sum())

        # ---- PRIORITY VIEW ----
        st.subheader("📊 Allocation by Priority")
        st.dataframe(
            allocation_df["Priority"]
            .value_counts()
            .reset_index()
            .rename(columns={"index": "Priority", "Priority": "Workers Allocated"})
        )

        # ---- SHORTFALL ----
        st.subheader("⚠️ Unfulfilled Requirements (Due to Manpower Shortage)")
        st.dataframe(shortfall_df)

        # ---- FINAL OUTPUT ----
        st.subheader("📤 Allocation Output")
        st.dataframe(allocation_df)

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
