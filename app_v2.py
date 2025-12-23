import streamlit as st
import pandas as pd

st.set_page_config(page_title="Worker Auto Allocation", layout="wide")

st.title("🏭 Smart Worker Allocation System")
st.caption("Priority-based, shortage-aware worker allocation")

attendance_file = st.file_uploader(
    "Upload Attendance Excel (with Day sheets)", type=["xlsx"]
)
requirements_file = st.file_uploader(
    "Upload Production Line Requirements Excel", type=["xlsx"]
)

# ---- WHAT IF SLIDER ----
extra_workers = st.slider(
    "What-if: Additional workers available",
    min_value=0, max_value=20, value=0
)

if attendance_file and requirements_file:

    attendance_xl = pd.ExcelFile(attendance_file, engine="openpyxl")
    day = st.selectbox("Select Day", attendance_xl.sheet_names)

    attendance_df = attendance_xl.parse(day)
    requirements_df = pd.read_excel(requirements_file, engine="openpyxl")

    # Simulate extra workers
    simulated_attendance = attendance_df.copy()
    for i in range(extra_workers):
        simulated_attendance = pd.concat([simulated_attendance, attendance_df.sample(1)], ignore_index=True)

    st.subheader("📋 Attendance Preview")
    st.dataframe(attendance_df.head())

    if st.button("🚀 Auto Allocate Workers"):

        priority_map = {"High": 1, "Medium": 2, "Low": 3}
        requirements_df["Priority_Order"] = requirements_df["Priority"].map(priority_map)
        requirements_df = requirements_df.sort_values("Priority_Order")

        simulated_attendance["Assigned"] = False
        allocations = []
        line_stats = []

        available_workers = len(simulated_attendance)

        for _, req in requirements_df.iterrows():

            skill = req["Skill"]
            required = req["Required_Workers"]
            line = req["Production_Line"]
            priority = req["Priority"]

            if priority == "High":
                eligible = simulated_attendance[
                    (simulated_attendance["Skill"] == skill) &
                    (simulated_attendance["Assigned"] == False)
                ].sort_values(by="Skill_Level", ascending=False)
            else:
                eligible = simulated_attendance[
                    (simulated_attendance["Skill"] == skill) &
                    (simulated_attendance["Assigned"] == False)
                ]

            allocated_count = min(len(eligible), required, available_workers)
            selected = eligible.head(allocated_count)

            simulated_attendance.loc[selected.index, "Assigned"] = True
            available_workers -= allocated_count

            for _, w in selected.iterrows():
                allocations.append({
                    "Worker_ID": w["Worker_ID"],
                    "Name": w["Name"],
                    "Skill": w["Skill"],
                    "Skill_Level": w["Skill_Level"],
                    "Production_Line": line,
                    "Priority": priority,
                    "Override": "No"
                })

            fulfilment = allocated_count / required if required else 1
            if fulfilment >= 0.9:
                status = "🟢 Green"
            elif fulfilment >= 0.7:
                status = "🟠 Amber"
            else:
                status = "🔴 Red"

            line_stats.append({
                "Production_Line": line,
                "Skill": skill,
                "Required": required,
                "Allocated": allocated_count,
                "Fulfilment_%": round(fulfilment * 100, 1),
                "Line_Status": status
            })

        allocation_df = pd.DataFrame(allocations)
        line_status_df = pd.DataFrame(line_stats)

        # ---- SUPERVISOR OVERRIDE ----
        st.subheader("✍️ Supervisor Override (Optional)")
        override_worker = st.selectbox(
            "Select Worker to Reassign",
            allocation_df["Worker_ID"].unique()
        )
        new_line = st.text_input("New Production Line")
        reason = st.text_area("Reason for override")

        if st.button("Apply Override") and new_line and reason:
            allocation_df.loc[
                allocation_df["Worker_ID"] == override_worker,
                ["Production_Line", "Override"]
            ] = [new_line, f"Yes: {reason}"]

            st.success("Override applied and logged")

        # ---- DASHBOARD ----
        st.subheader("📈 Manpower Summary")
        st.metric("Actual Present", len(attendance_df))
        st.metric("Simulated Present", len(simulated_attendance))
        st.metric("Total Allocated", len(allocation_df))

        st.subheader("🚦 Line Health Status")
        st.dataframe(line_status_df)

        st.subheader("📤 Final Allocation")
        st.dataframe(allocation_df)

        output_file = f"{day}_Auto_Allocation_Advanced.xlsx"
        allocation_df.to_excel(output_file, index=False)

        with open(output_file, "rb") as f:
            st.download_button(
                "⬇️ Download Final Allocation",
                f,
                file_name=output_file
            )

else:
    st.info("Upload both Excel files to proceed")
